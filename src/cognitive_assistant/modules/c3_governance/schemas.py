"""Contratos y esquemas de datos para la Capa 3: Gobernanza y Control de Riesgos."""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ViolationType(str, Enum):
    """Taxonomía de tipos de violación de seguridad cognitiva."""
    NONE = "none"
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    SYSTEM_PROMPT_LEAK = "system_prompt_leak"
    PAYLOAD_OVERSIZED = "payload_oversized"
    INVALID_CONTROL_CHARS = "invalid_control_chars"


class RiskEvaluation(BaseModel):
    """Resultado de la evaluación de riesgo perimétrico sobre un estímulo entrante."""
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Puntuación de riesgo normalizada (0.0 a 1.0)")
    allowed: bool = Field(..., description="Determina si el estímulo está autorizado a entrar al Ejecutivo Cognitivo")
    violation_type: ViolationType = Field(default=ViolationType.NONE, description="Tipo de infracción identificada")
    reason: Optional[str] = Field(default=None, description="Justificación técnica del bloqueo o advertencia")
    sanitized_content: str = Field(..., description="Contenido limpio tras sanitización defensiva")
    trace_id: str = Field(..., description="Identificador de trazabilidad distribuida")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos forenses de la evaluación")


class ProblemDetails(BaseModel):
    """Estructura de error conforme a RFC 7807 (Problem Details for HTTP APIs)."""
    type: str = Field(default="urn:cognitive-assistant:error:security-violation", description="URI del tipo de error")
    title: str = Field(default="Security Policy Violation", description="Resumen breve del error")
    status: int = Field(default=403, description="Código de estado HTTP")
    detail: str = Field(..., description="Descripción detallada de la violación")
    instance: str = Field(..., description="URI de la transacción o trace_id")
    violation_type: str = Field(..., description="Categoría de infracción detectada")
