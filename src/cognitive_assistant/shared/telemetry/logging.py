import logging
import sys
from typing import Optional
from cognitive_assistant.shared.telemetry.trace import get_trace_id


class TraceIdFilter(logging.Filter):
    """Filtro de logging que inyecta automáticamente el trace_id actual en cada LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()
        return True


def setup_logging(level: str = "INFO") -> None:
    """Configura el sistema centralizado de logging con inyección de trace_id."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    log_format = (
        "%(asctime)s | %(levelname)-7s | [%(name)s] [trace_id=%(trace_id)s] %(message)s"
    )

    formatter = logging.Formatter(fmt=log_format, datefmt="%Y-%m-%d %H:%M:%S")

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    handler.setFormatter(formatter)
    handler.addFilter(TraceIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Reemplazar handlers existentes para evitar logs duplicados
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Reducir verbosidad de librerías externas si es necesario
    logging.getLogger("uvicorn.access").addFilter(TraceIdFilter())


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Obtiene un logger configurado con el nombre dado."""
    return logging.getLogger(name or "cognitive_assistant")
