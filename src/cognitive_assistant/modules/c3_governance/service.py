"""Servicio de Gobernanza y Control de Riesgos Perimétricos (Capa 3)."""
import time
from typing import Optional
from cognitive_assistant.modules.c3_governance.prompt_guard import PromptGuard
from cognitive_assistant.modules.c3_governance.sanitizer import InputSanitizer
from cognitive_assistant.modules.c3_governance.schemas import RiskEvaluation, ViolationType
from cognitive_assistant.shared.telemetry.logging import get_logger
from cognitive_assistant.shared.telemetry.trace import get_trace_id

logger = get_logger("cognitive_assistant.governance")


class GovernanceService:
    """Orquestador de políticas de seguridad, sanitización y filtrado de estímulos."""

    RISK_THRESHOLD = 0.70

    @classmethod
    def evaluate_stimulus(
        cls,
        content: str,
        trace_id: Optional[str] = None,
    ) -> RiskEvaluation:
        """
        Ejecuta la inspección de seguridad perimétrica completa:
        1. Sanitización de caracteres de control y normalización Unicode NFKC.
        2. Detección heurística de firmas adversarias con PromptGuard.
        3. Clasificación de riesgo y decisión de acceso.
        """
        start_time = time.perf_counter()
        current_trace = trace_id or get_trace_id()

        # 1. Sanitización
        sanitized_content, had_invalid_chars, was_oversized = InputSanitizer.sanitize(content)

        if had_invalid_chars:
            logger.warning(
                "Estímulo contiene caracteres de control o nulos. Sanitizados defensivamente (trace_id=%s)",
                current_trace,
            )

        if was_oversized:
            eval_time_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning(
                "Estímulo excede la longitud máxima permitida (%d chars). Rechazado (trace_id=%s)",
                len(content),
                current_trace,
            )
            return RiskEvaluation(
                risk_score=0.90,
                allowed=False,
                violation_type=ViolationType.PAYLOAD_OVERSIZED,
                reason="El contenido excede el tamaño máximo permitido de 8,000 caracteres.",
                sanitized_content=sanitized_content,
                trace_id=current_trace,
                metadata={"duration_ms": round(eval_time_ms, 3)},
            )

        # 2. Análisis heurístico adversario
        risk_score, violation_type, signatures = PromptGuard.evaluate(sanitized_content)
        allowed = risk_score < cls.RISK_THRESHOLD

        eval_time_ms = (time.perf_counter() - start_time) * 1000.0

        reason: Optional[str] = None
        if not allowed:
            if violation_type == ViolationType.JAILBREAK_ATTEMPT:
                reason = "Infracción de gobernanza: Intento de Jailbreak / evasión de límites detectado."
            elif violation_type == ViolationType.PROMPT_INJECTION:
                reason = "Infracción de gobernanza: Intento de Prompt Injection / anulación de instrucciones detectado."
            elif violation_type == ViolationType.SYSTEM_PROMPT_LEAK:
                reason = "Infracción de gobernanza: Intento de exfiltración de instrucciones de sistema detectado."
            else:
                reason = "Infracción de gobernanza perimétrica detectada."

            logger.warning(
                "AMENAZA BLOQUEADA en Capa 3: tipo='%s', score=%.2f, firmas=%s, latencia=%.2f ms, trace_id=%s",
                violation_type.value,
                risk_score,
                signatures,
                eval_time_ms,
                current_trace,
            )
        else:
            logger.debug(
                "Estímulo perimétrico aprobado: score=%.2f, latencia=%.2f ms, trace_id=%s",
                risk_score,
                eval_time_ms,
                current_trace,
            )

        return RiskEvaluation(
            risk_score=risk_score,
            allowed=allowed,
            violation_type=violation_type,
            reason=reason,
            sanitized_content=sanitized_content,
            trace_id=current_trace,
            metadata={
                "signatures": signatures,
                "duration_ms": round(eval_time_ms, 3),
                "sanitized": had_invalid_chars,
            },
        )
