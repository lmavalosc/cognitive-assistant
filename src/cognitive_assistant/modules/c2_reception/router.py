import time
from typing import Any, Union
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from cognitive_assistant.modules.c2_reception.schemas import (
    DeliberateRequest,
    DeliberateResponse,
    HealthResponse,
    ReceptionMessageRequest,
    ReceptionMessageResponse,
)
from cognitive_assistant.modules.c3_governance.service import GovernanceService
from cognitive_assistant.modules.c4_executive.graph import execute_cognitive_cycle
from cognitive_assistant.modules.c8_effectors.dispatcher import EffectorDispatcher
from cognitive_assistant.settings import settings
from cognitive_assistant.shared.infrastructure.audit import AuditService
from cognitive_assistant.shared.infrastructure.auth import Principal, require_api_key
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
async def receive_message(
    payload: ReceptionMessageRequest,
    principal: Principal = Depends(require_api_key),
) -> Union[ReceptionMessageResponse, JSONResponse]:
    """Recibe un mensaje en C2, valida gobernanza en C3 y lo canaliza hacia C8 Efectores con auditoría."""
    start_time = time.perf_counter()
    current_trace = get_trace_id()
    logger.info("Mensaje recibido en C2: origen='%s', user_id='%s'", payload.source, principal.user_id)

    # Inspección de Gobernanza
    evaluation = GovernanceService.evaluate_stimulus(payload.content, trace_id=current_trace)
    if not evaluation.allowed:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        await AuditService.record_transaction(
            trace_id=current_trace,
            endpoint="/reception/message",
            channel=payload.source,
            status=status.HTTP_403_FORBIDDEN,
            duration_ms=round(duration_ms, 2),
            summary=payload.content,
            metadata={
                "user_id": principal.user_id,
                "violation_type": evaluation.violation_type.value,
                "risk_score": evaluation.risk_score,
                "reason": evaluation.reason,
                "security_violation": True,
            },
            security_violation=True,
        )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "type": "urn:cognitive-assistant:error:security-violation",
                "title": "Security Policy Violation",
                "status": 403,
                "detail": evaluation.reason,
                "instance": current_trace,
                "violation_type": evaluation.violation_type.value,
            },
            headers={"X-Trace-ID": current_trace},
        )

    dispatcher = EffectorDispatcher()
    dispatch_result = await dispatcher.dispatch(
        event_type="reception.message",
        payload={"content": evaluation.sanitized_content, "source": payload.source, "meta": payload.metadata},
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
    "/api/v1/chat",
    response_model=DeliberateResponse,
    status_code=status.HTTP_200_OK,
    summary="Endpoint canónico de deliberación cognitiva multi-turno",
)
@router.post(
    "/reception/deliberate",
    response_model=DeliberateResponse,
    status_code=status.HTTP_200_OK,
    summary="Alias de ciclo cognitivo deliberativo completo",
)
async def deliberate_message(
    payload: DeliberateRequest,
    request: Request,
    principal: Principal = Depends(require_api_key),
) -> Union[DeliberateResponse, JSONResponse]:
    """
    Ejecuta el ciclo cognitivo con inspección perimétrica en Capa 3 (Gobernanza)
    y persistencia en Plano B:
    C2 Ingesta -> C3 Gobernanza (PromptGuard / Sanitización)
    -> [Si Aprobado] C5 Recuperación Memoria (mem0) + Redis WM -> C4 Planificación (LangGraph)
    -> Plano A Inferencia (LiteLLM) -> C5 Consolidación -> C8 Efector -> Auditoría DB.
    -> [Si Rechazado] HTTP 403 (RFC 7807) + Auditoría de seguridad persistente en DB.
    """
    start_time = time.perf_counter()
    current_trace = get_trace_id()
    endpoint_path = request.url.path if request else "/api/v1/chat"
    effective_user_id = principal.user_id if principal.api_key != "local-dev" else (payload.user_id or principal.user_id)
    logger.info(
        "Iniciando deliberación cognitiva en C2 (endpoint='%s') para user_id='%s', session_id='%s', trace_id=%s",
        endpoint_path,
        effective_user_id,
        payload.session_id,
        current_trace,
    )

    # 1. Capa 3: Inspección de Gobernanza y Cortafuegos Cognitivo
    evaluation = GovernanceService.evaluate_stimulus(payload.content, trace_id=current_trace)
    if not evaluation.allowed:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        # Registrar violación de seguridad de forma persistente en PostgreSQL
        await AuditService.record_transaction(
            trace_id=current_trace,
            endpoint=endpoint_path,
            channel="http",
            status=status.HTTP_403_FORBIDDEN,
            duration_ms=round(duration_ms, 2),
            summary=payload.content,
            session_id=payload.session_id,
            metadata={
                "user_id": effective_user_id,
                "violation_type": evaluation.violation_type.value,
                "risk_score": evaluation.risk_score,
                "reason": evaluation.reason,
                "security_violation": True,
            },
            security_violation=True,
        )

        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "type": "urn:cognitive-assistant:error:security-violation",
                "title": "Security Policy Violation",
                "status": 403,
                "detail": evaluation.reason,
                "instance": current_trace,
                "violation_type": evaluation.violation_type.value,
            },
            headers={"X-Trace-ID": current_trace},
        )

    # 2. Capa 4: Ejecutar ciclo cognitivo con estímulo sanitizado y user_id autenticado
    final_state = await execute_cognitive_cycle(
        message=evaluation.sanitized_content,
        user_id=effective_user_id,
        session_id=payload.session_id,
        metadata=payload.metadata,
    )

    # 3. Capa 8: Despachar a efectores
    dispatcher = EffectorDispatcher()
    await dispatcher.dispatch(
        event_type="cognitive.response",
        payload={
            "response": final_state.get("response", ""),
            "plan": final_state.get("plan", []),
            "user_id": effective_user_id,
            "session_id": payload.session_id,
        },
    )


    duration_ms = (time.perf_counter() - start_time) * 1000.0
    await AuditService.record_transaction(
        trace_id=current_trace,
        endpoint=endpoint_path,
        channel="http",
        status=status.HTTP_200_OK,
        duration_ms=round(duration_ms, 2),
        summary=payload.content,
        session_id=payload.session_id,
        metadata={
            "user_id": payload.user_id,
            "plan_steps": len(final_state.get("plan", [])),
            "risk_score": evaluation.risk_score,
        },
        security_violation=False,
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
