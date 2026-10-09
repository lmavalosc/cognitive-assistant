"""Middleware de Limitación de Tasa (Rate Limiting) basado en Redis.

Implementa un contador de ventana deslizante / token bucket sobre Redis para mitigar
ataques de denegación de servicio (DoS) y consumo abusivo de recursos.
Aplica degradación elegante ante caídas de Redis (fallback permisivo).
"""

from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from cognitive_assistant.settings import settings
from cognitive_assistant.shared.infrastructure.redis_client import get_redis_client
from cognitive_assistant.shared.telemetry.logging import get_logger
from cognitive_assistant.shared.telemetry.trace import get_trace_id

logger = get_logger("cognitive_assistant.infrastructure.rate_limit")

EXCLUDED_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware que aplica cuotas de peticiones por cliente usando Redis."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Si rate limiting está desactivado o la ruta está exenta, continuar directamente
        if not settings.rate_limit_enabled or request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        # 2. Identificar al cliente (por X-API-Key o IP de origen)
        api_key = request.headers.get("X-API-Key")
        client_host = request.client.host if request.client else "unknown_client"
        client_id = f"key_{api_key[:8]}" if api_key else f"ip_{client_host}"

        trace_id = get_trace_id()
        redis_key = f"rate_limit:{client_id}"

        # 3. Interrogar Redis de forma no bloqueante
        try:
            client = await get_redis_client()
            # Incrementar contador atómicamente
            current_count = await client.incr(redis_key)
            if current_count == 1:
                # Fijar expiración de la ventana en segundos
                await client.expire(redis_key, settings.rate_limit_window_seconds)

            if current_count > settings.rate_limit_requests:
                logger.warning(
                    "Límite de tasa excedido para %s (conteo=%d, límite=%d). trace_id=%s",
                    client_id,
                    current_count,
                    settings.rate_limit_requests,
                    trace_id,
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "type": "urn:cognitive-assistant:error:rate-limit-exceeded",
                        "title": "Too Many Requests",
                        "status": 429,
                        "detail": f"Se ha excedido el límite de {settings.rate_limit_requests} peticiones por ventana de {settings.rate_limit_window_seconds}s.",
                        "instance": trace_id,
                    },
                    headers={
                        "X-Trace-ID": trace_id,
                        "Retry-After": str(settings.rate_limit_window_seconds),
                    },
                )
        except Exception as exc:
            # Degradación elegante: Si Redis no está disponible o falla, permitir la petición pero loggear WARN
            logger.warning(
                "Fallo en RateLimitMiddleware sobre Redis (%s). Aplicando fallback permisivo para trace_id=%s",
                exc,
                trace_id,
            )

        return await call_next(request)
