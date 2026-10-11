"""Capa 3.c: Filtro Perimétrico de Salida (Output Guard).

Inspecciona y sanitiza las respuestas salientes generadas por el modelo antes
de ser despachadas a efectores o retornadas al cliente, evitando fugas de
secretos, llaves de API, credenciales o PII (Personally Identifiable Information).
"""

import re
from typing import List, Optional
from pydantic import BaseModel, Field

from cognitive_assistant.shared.telemetry.logging import get_logger
from cognitive_assistant.shared.telemetry.trace import get_trace_id

logger = get_logger("cognitive_assistant.governance.output_guard")


class OutputFilterResult(BaseModel):
    """Resultado del filtrado e inspección perimétrica de salida."""

    sanitized_content: str = Field(..., description="Contenido redactado y seguro para el usuario")
    leak_detected: bool = Field(default=False, description="Indica si se detectó un intento de fuga de información")
    reasons: List[str] = Field(default_factory=list, description="Lista de infracciones detectadas")
    trace_id: str = Field(..., description="Identificador de traza asociado")


# Patrones regex para detección y ofuscación de secretos en salida
_SECRET_PATTERNS = [
    # Google API Keys (AIzaSy...)
    (re.compile(r"\bAIzaSy[a-zA-Z0-9_\-]{33}\b"), "[REDACTED_GOOGLE_API_KEY]"),
    # OpenAI & Standard API Keys
    (re.compile(r"\b(?:sk-[a-zA-Z0-9_\-]{20,}|ghp_[a-zA-Z0-9]{20,}|key-[a-zA-Z0-9]{20,})\b", re.IGNORECASE), "[REDACTED_API_KEY]"),
    # Bearer Tokens
    (re.compile(r"\bBearer\s+[a-zA-Z0-9_\-\.]{25,}\b", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    # Database URIs con credenciales (postgres://user:pass@host)
    (re.compile(r"\b(postgres(?:ql)?|redis|mongodb)://[^:]+:[^@]+@[^\s/]+", re.IGNORECASE), r"\1://[REDACTED_USER]:[REDACTED_PASS]@[REDACTED_HOST]"),
    # Passwords y tokens en texto plano
    (re.compile(r"(?i)\b(password|contrase[ñn]a|secret_token|access_token)\s*[:=]\s*(\S+)", re.IGNORECASE), r"\1=[REDACTED_SECRET]"),
    # Tarjetas de crédito
    (re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"), "[REDACTED_CREDIT_CARD]"),
    # Claves privadas PEM
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
]


class OutputGuard:
    """Guardia perimétrico de salida para respuestas cognitivas."""

    @classmethod
    def filter_response(cls, text: str, trace_id: Optional[str] = None) -> OutputFilterResult:
        """
        Inspecciona el texto saliente, ofusca secretos o credenciales detectadas
        y emite un registro de auditoría si hubo tentativa de exfiltración.
        """
        current_trace = trace_id or get_trace_id()
        if not text:
            return OutputFilterResult(
                sanitized_content="",
                leak_detected=False,
                reasons=[],
                trace_id=current_trace,
            )

        sanitized = text
        leak_detected = False
        reasons = []

        for pattern, replacement in _SECRET_PATTERNS:
            if pattern.search(sanitized):
                leak_detected = True
                reasons.append(f"Patrón de datos confidenciales detectado ({pattern.pattern[:30]}...)")
                sanitized = pattern.sub(replacement, sanitized)

        if leak_detected:
            logger.warning(
                "GOBERNANZA DE SALIDA (3.c) INTERVENIDA: Fuga de datos confidenciales neutralizada en respuesta (trace_id=%s, infracciones=%d)",
                current_trace,
                len(reasons),
            )

        return OutputFilterResult(
            sanitized_content=sanitized,
            leak_detected=leak_detected,
            reasons=reasons,
            trace_id=current_trace,
        )
