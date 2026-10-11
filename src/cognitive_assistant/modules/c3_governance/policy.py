"""Capa 3: Gobernanza de Acción y Control de Políticas sobre Herramientas (Punto b).

Garantiza que ninguna herramienta periférica sea invocada de forma autónoma sin pasar
por un control de riesgo, verificación de autorización HITL y validación defensiva de parámetros.
"""

import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from cognitive_assistant.shared.telemetry.logging import get_logger
from cognitive_assistant.shared.telemetry.trace import get_trace_id
from cognitive_assistant.shared.tools.registry import (
    ToolDefinition,
    ToolRequest,
    ToolRiskLevel,
)
from cognitive_assistant.shared.tools.url_validator import validate_outbound_url

logger = get_logger("cognitive_assistant.governance.policy")


class ActionPolicyDecision(BaseModel):
    """Decisión de política emitida por la Gobernanza de Acción (Capa 3.b)."""
    allowed: bool = Field(..., description="Determina si la acción tiene permiso para ejecutarse")
    risk_level: ToolRiskLevel = Field(..., description="Nivel de riesgo determinado para la herramienta")
    requires_hitl: bool = Field(default=False, description="Indica si la acción requiere confirmación humana")
    violation_type: Optional[str] = Field(default=None, description="Categoría de infracción si fue rechazada")
    reason: Optional[str] = Field(default=None, description="Motivo técnico de la decisión o rechazo")
    trace_id: str = Field(..., description="Identificador de trazabilidad distribuida")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos forenses de la evaluación")


# Patrones de inyección de comandos o secuencias destructivas en argumentos de texto
_DANGEROUS_COMMAND_PATTERNS = [
    re.compile(r"\brm\s+-[rRfF]+\b", re.IGNORECASE),
    re.compile(r";\s*(rm|del|shutdown|format|mkfs)\b", re.IGNORECASE),
    re.compile(r"\|\s*(bash|sh|cmd|powershell)\b", re.IGNORECASE),
    re.compile(r"`.*?`"),
    re.compile(r"\$\(.*?\)", re.IGNORECASE),
]


class ActionPolicyService:
    """Servicio de control de políticas de acción para herramientas cognitivas."""

    @classmethod
    def evaluate_action(
        cls,
        request: ToolRequest,
        tool_definition: Optional[ToolDefinition],
    ) -> ActionPolicyDecision:
        """
        Evalúa el permiso de ejecución para un ToolRequest antes de que toque cualquier periférico:
        1. Valida que la herramienta esté formalmente registrada en el catálogo seguro.
        2. Aplica validación anti-SSRF si algún parámetro contiene una URL.
        3. Inspecciona argumentos contra patrones de inyección de comandos en parámetros no diseñados para ello.
        4. Verifica si el nivel de riesgo requiere aprobación Human-in-the-Loop (CRITICAL).
        """
        current_trace = request.trace_id or get_trace_id()

        # 1. Herramienta no registrada
        if tool_definition is None:
            logger.warning(
                "GOBERNANZA DE ACCIÓN (3.b) BLOQUEADA: Herramienta '%s' no registrada (trace_id=%s)",
                request.tool_name,
                current_trace,
            )
            return ActionPolicyDecision(
                allowed=False,
                risk_level=ToolRiskLevel.HIGH,
                requires_hitl=False,
                violation_type="unauthorized_tool",
                reason=f"La herramienta '{request.tool_name}' no existe en el catálogo seguro de herramientas.",
                trace_id=current_trace,
            )

        risk_level = tool_definition.risk_level

        # 2. Validación anti-SSRF en argumentos que representen URLs
        for arg_name, arg_val in request.arguments.items():
            if isinstance(arg_val, str) and (
                arg_name.lower() in ("url", "target_url", "link") or
                arg_val.startswith("http://") or arg_val.startswith("https://")
            ):
                try:
                    validate_outbound_url(arg_val)
                except ValueError as ssrf_err:
                    logger.warning(
                        "GOBERNANZA DE ACCIÓN (3.b) BLOQUEADA [ANTI-SSRF]: tool='%s', url='%s', error='%s' (trace_id=%s)",
                        request.tool_name,
                        arg_val,
                        ssrf_err,
                        current_trace,
                    )
                    return ActionPolicyDecision(
                        allowed=False,
                        risk_level=ToolRiskLevel.CRITICAL,
                        requires_hitl=False,
                        violation_type="ssrf_attempt",
                        reason=f"Violación de política perimétrica anti-SSRF: {ssrf_err}",
                        trace_id=current_trace,
                        metadata={"target_url": arg_val},
                    )

        # 3. Detección de inyección de comandos en herramientas no-shell
        if request.tool_name != "system_command_mock":
            for arg_name, arg_val in request.arguments.items():
                if isinstance(arg_val, str):
                    for pattern in _DANGEROUS_COMMAND_PATTERNS:
                        if pattern.search(arg_val):
                            logger.warning(
                                "GOBERNANZA DE ACCIÓN (3.b) BLOQUEADA [INYECCIÓN DE COMANDO]: tool='%s', arg='%s' (trace_id=%s)",
                                request.tool_name,
                                arg_name,
                                current_trace,
                            )
                            return ActionPolicyDecision(
                                allowed=False,
                                risk_level=ToolRiskLevel.CRITICAL,
                                requires_hitl=False,
                                violation_type="command_injection_attempt",
                                reason=f"Patrón de comando potencialmente destructivo detectado en el argumento '{arg_name}'.",
                                trace_id=current_trace,
                                metadata={"argument": arg_name},
                            )

        # 4. Verificación de Human-in-the-Loop (HITL) para herramientas CRÍTICAS
        if risk_level == ToolRiskLevel.CRITICAL or tool_definition.requires_approval:
            if not request.hitl_approved:
                logger.warning(
                    "GOBERNANZA DE ACCIÓN (3.b) DETENIDA [HITL REQUERIDO]: tool='%s', trace_id=%s",
                    request.tool_name,
                    current_trace,
                )
                return ActionPolicyDecision(
                    allowed=False,
                    risk_level=ToolRiskLevel.CRITICAL,
                    requires_hitl=True,
                    violation_type="hitl_approval_required",
                    reason="Operación de riesgo CRÍTICO: requiere autorización explícita de un operador humano (HITL).",
                    trace_id=current_trace,
                    metadata={"tool_name": request.tool_name},
                )

        # 5. Aprobado
        logger.info(
            "GOBERNANZA DE ACCIÓN (3.b) APROBADA: tool='%s', risk=%s, trace_id=%s",
            request.tool_name,
            risk_level.value,
            current_trace,
        )
        return ActionPolicyDecision(
            allowed=True,
            risk_level=risk_level,
            requires_hitl=False,
            reason=None,
            trace_id=current_trace,
            metadata={"tool_name": request.tool_name},
        )
