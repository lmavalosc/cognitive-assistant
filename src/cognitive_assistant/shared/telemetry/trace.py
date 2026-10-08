import uuid
from contextvars import ContextVar, Token
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

TRACE_HEADER = "X-Trace-ID"
_trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="-")


def generate_trace_id() -> str:
    """Genera un identificador único de trazabilidad (UUID4 hex de 32 caracteres)."""
    return uuid.uuid4().hex


def get_trace_id() -> str:
    """Obtiene el trace_id del contexto de ejecución actual."""
    return _trace_id_ctx.get()


def set_trace_id(trace_id: str) -> Token[str]:
    """Establece el trace_id en el contexto actual."""
    return _trace_id_ctx.set(trace_id)


def reset_trace_id(token: Token[str]) -> None:
    """Restaura el trace_id del contexto al token previo."""
    _trace_id_ctx.reset(token)


class TraceMiddleware(BaseHTTPMiddleware):
    """
    Middleware HTTP que asegura que cada petición tenga un trace_id:
    - Extrae X-Trace-ID del encabezado entrante si existe.
    - Genera uno nuevo si no está presente.
    - Lo propaga en el ContextVar para logging.
    - Lo inyecta en el encabezado de respuesta HTTP (X-Trace-ID).
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming_trace_id = request.headers.get("x-trace-id") or request.headers.get("x-request-id")
        trace_id = incoming_trace_id.strip() if incoming_trace_id else generate_trace_id()

        token = set_trace_id(trace_id)
        request.state.trace_id = trace_id

        try:
            response = await call_next(request)
            response.headers[TRACE_HEADER] = trace_id
            return response
        finally:
            reset_trace_id(token)
