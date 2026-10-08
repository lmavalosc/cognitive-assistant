from typing import Any, Dict
from cognitive_assistant.shared.telemetry.logging import get_logger
from cognitive_assistant.shared.telemetry.trace import get_trace_id

logger = get_logger("cognitive_assistant.effectors")


class EffectorDispatcher:
    """Despachador del Tronco Encefálico (Efectores C8) para canalizar salidas o eventos."""

    def __init__(self) -> None:
        pass

    async def dispatch(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Despacha un evento transaccional hacia los canales de salida configurados.
        Registra la traza correspondiente en los logs estructurados.
        """
        current_trace = get_trace_id()
        logger.info(
            "Despachando evento efector: tipo='%s', payload_keys=%s",
            event_type,
            list(payload.keys()),
        )

        return {
            "dispatched_at": "now",
            "event_type": event_type,
            "trace_id": current_trace,
            "status": "acknowledged",
        }
