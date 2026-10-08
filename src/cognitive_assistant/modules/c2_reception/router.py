from fastapi import APIRouter, status
from cognitive_assistant.modules.c2_reception.schemas import (
    HealthResponse,
    ReceptionMessageRequest,
    ReceptionMessageResponse,
)
from cognitive_assistant.modules.c8_effectors.dispatcher import EffectorDispatcher
from cognitive_assistant.settings import settings
from cognitive_assistant.shared.telemetry.logging import get_logger
from cognitive_assistant.shared.telemetry.trace import get_trace_id

router = APIRouter(prefix="", tags=["Recepción & Núcleo"])
logger = get_logger("cognitive_assistant.reception")


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Verificación del estado de salud del sistema",
)
async def health_check() -> HealthResponse:
    """Endpoint de health check con esquema del tronco encefálico."""
    logger.info("Health check")
    return HealthResponse(
        status="ok",
        service="cognitive-assistant",
        environment=settings.app_env,
        version="0.1.0",
    )


@router.post(
    "/reception/message",
    response_model=ReceptionMessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Recepción transaccional de mensajes",
)
async def receive_message(payload: ReceptionMessageRequest) -> ReceptionMessageResponse:
    """Recibe un mensaje en C2 y lo canaliza hacia C8 Efectores."""
    current_trace = get_trace_id()
    logger.info("Mensaje recibido en C2: origen='%s'", payload.source)

    dispatcher = EffectorDispatcher()
    dispatch_result = await dispatcher.dispatch(
        event_type="reception.message",
        payload={"content": payload.content, "source": payload.source, "meta": payload.metadata},
    )

    return ReceptionMessageResponse(
        status="accepted",
        trace_id=current_trace,
        dispatched=True,
        details=dispatch_result,
    )
