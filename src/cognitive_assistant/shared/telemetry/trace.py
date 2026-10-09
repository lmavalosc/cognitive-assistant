import logging
import re
import uuid
from contextvars import ContextVar
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("cognitive_assistant.telemetry.trace")
SAFE_TRACE_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,64}$")

trace_id_ctx: ContextVar[str | None] = ContextVar(
    "trace_id",
    default=None,
)


def generate_trace_id() -> str:
    """Genera un identificador único UUID4."""
    return str(uuid.uuid4())


def get_trace_id() -> str:
    """Obtiene el trace_id del contexto actual, generando uno si no existe."""
    trace_id = trace_id_ctx.get()
    if trace_id is None:
        trace_id = generate_trace_id()
        trace_id_ctx.set(trace_id)
    return trace_id


def set_trace_id(trace_id: str):
    """Establece el trace_id en el contexto."""
    return trace_id_ctx.set(trace_id)


def reset_trace_id(token) -> None:
    """Restaura el trace_id previo."""
    trace_id_ctx.reset(token)


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Middleware HTTP para extraer o generar y propagar X-Trace-ID con validación de seguridad."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming_trace_id = request.headers.get("X-Trace-ID")
        if incoming_trace_id:
            if SAFE_TRACE_PATTERN.match(incoming_trace_id):
                trace_id = incoming_trace_id
            else:
                logger.warning(
                    "X-Trace-ID entrante no confiable o con formato peligroso ('%s'). Regenerando UUID limpio.",
                    incoming_trace_id[:64],
                )
                trace_id = generate_trace_id()
        else:
            trace_id = generate_trace_id()

        token = trace_id_ctx.set(trace_id)
        request.state.trace_id = trace_id

        try:
            response: Response = await call_next(request)
            response.headers["X-Trace-ID"] = trace_id
            return response
        finally:
            trace_id_ctx.reset(token)


# Alias de compatibilidad
TraceMiddleware = TraceIDMiddleware

