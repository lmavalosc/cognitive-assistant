import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional
from cognitive_assistant.shared.telemetry.trace import get_trace_id, trace_id_ctx


class JsonFormatter(logging.Formatter):
    """Formateador de logs en JSON con inyección de trace_id."""

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        trace_id = trace_id_ctx.get()
        if trace_id:
            log["trace_id"] = trace_id

        return json.dumps(log)


class TraceIdFilter(logging.Filter):
    """Filtro para inyectar trace_id en registros sin generar identificadores artificiales."""

    def filter(self, record: logging.LogRecord) -> bool:
        tid = trace_id_ctx.get()
        if tid:
            record.trace_id = tid
        return True



def setup_logging(level: str = "INFO") -> None:
    """Configura el logging raíz con salida JSON."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(TraceIdFilter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Obtiene un logger por nombre."""
    return logging.getLogger(name or "cognitive_assistant")
