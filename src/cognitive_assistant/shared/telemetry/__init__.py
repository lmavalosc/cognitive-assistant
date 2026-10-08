"""Módulo de telemetría: tracing y logging estructurado."""

from cognitive_assistant.shared.telemetry.logging import get_logger, setup_logging
from cognitive_assistant.shared.telemetry.trace import (
    TraceMiddleware,
    generate_trace_id,
    get_trace_id,
    reset_trace_id,
    set_trace_id,
)

__all__ = [
    "TraceMiddleware",
    "generate_trace_id",
    "get_logger",
    "get_trace_id",
    "reset_trace_id",
    "set_trace_id",
    "setup_logging",
]
