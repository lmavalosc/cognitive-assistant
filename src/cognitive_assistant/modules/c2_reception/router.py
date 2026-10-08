import time
from fastapi import APIRouter, status
from cognitive_assistant.modules.c2_reception.schemas import (
    DeliberateRequest,
    DeliberateResponse,
    HealthResponse,
    ReceptionMessageRequest,
    ReceptionMessageResponse,
)
from cognitive_assistant.modules.c4_executive.graph import execute_cognitive_cycle
from cognitive_assistant.modules.c8_effectors.dispatcher import EffectorDispatcher
from cognitive_assistant.settings import settings
from cognitive_assistant.shared.infrastructure.audit import AuditService
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
    """Recibe un mensaje en C2 y lo canaliza hacia C8 Efectores con auditoría."""
    start_time = time.perf_counter()
    current_trace = get_trace_id()
    logger.info("Mensaje recibido en C2: origen='%s'", payload.source)

    dispatcher = EffectorDispatcher()
    dispatch_result = await dispatcher.dispatch(
        event_type="reception.message",
        payload={"content": payload.content, "source": payload.source, "meta": payload.metadata},
    )

    duration_ms = (time.perf_counter() - start_time) * 1000.0
    await AuditService.record_transaction(
        trace_id=current_trace,
        endpoint="/reception/message",
        channel=payload.source,
        status=status.HTTP_202_ACCEPTED,
        duration_ms=round(duration_ms, 2),
        summary=payload.content,
        metadata=payload.metadata,
    )

    return ReceptionMessageResponse(
        status="accepted",
        trace_id=current_trace,
        dispatched=True,
        details=dispatch_result,
    )


@router.post(
    "/reception/deliberate",
    response_model=DeliberateResponse,
    status_code=status.HTTP_200_OK,
    summary="Ciclo cognitivo deliberativo completo",
)
async def deliberate_message(payload: DeliberateRequest) -> DeliberateResponse:
    """
    Ejecuta el ciclo cognitivo completo con persistencia en Plano B:
    C2 Ingesta -> C5 Recuperación Memoria (mem0) -> C4 Planificación (LangGraph)
    -> Plano A Inferencia (LiteLLM) -> C5 Consolidación -> C8 Efector -> Auditoría DB.
    """
    start_time = time.perf_counter()
    current_trace = get_trace_id()
    logger.info(
        "Iniciando deliberación cognitiva en C2 para user_id='%s', trace_id=%s",
        payload.user_id,
        current_trace,
    )

    final_state = await execute_cognitive_cycle(
        message=payload.content,
        user_id=payload.user_id,
        session_id=payload.session_id,
        metadata=payload.metadata,
    )

    dispatcher = EffectorDispatcher()
    await dispatcher.dispatch(
        event_type="cognitive.response",
        payload={
            "response": final_state.get("response", ""),
            "plan": final_state.get("plan", []),
            "user_id": payload.user_id,
            "session_id": payload.session_id,
        },
    )

    duration_ms = (time.perf_counter() - start_time) * 1000.0
    await AuditService.record_transaction(
        trace_id=current_trace,
        endpoint="/reception/deliberate",
        channel="http",
        status=status.HTTP_200_OK,
        duration_ms=round(duration_ms, 2),
        summary=payload.content,
        session_id=payload.session_id,
        metadata={"user_id": payload.user_id, "plan_steps": len(final_state.get("plan", []))},
    )

    return DeliberateResponse(
        status=final_state.get("status", "completed"),
        trace_id=current_trace,
        session_id=payload.session_id,
        response=final_state.get("response", ""),
        plan=final_state.get("plan", []),
        context_memories=final_state.get("context_memories", []),
        dispatched=True,
    )


