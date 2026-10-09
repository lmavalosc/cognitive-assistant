"""Sanitizador y Enmascarador de Datos Personales y Secretos (PII Scrubbing).

Garantiza que información de identificación personal (PII), secretos de autenticación
y contraseñas sean anonimizados antes de persistirse en registros de auditoría o telemetría.
"""

import re

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)
CREDIT_CARD_PATTERN = re.compile(
    r"\b(?:\d{4}[ -]?){3}\d{4}\b"
)
API_KEY_PATTERN = re.compile(
    r"\b(?:sk-[a-zA-Z0-9_\-]{20,}|ghp_[a-zA-Z0-9]{20,}|bearer\s+[a-zA-Z0-9_\-\.]{25,}|key-[a-zA-Z0-9]{20,})\b",
    re.IGNORECASE,
)
PASSWORD_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(password|contrase[ñn]a|passwd|secret|token)\s*([:=])\s*(\S+)"
)


def scrub_pii(text: str) -> str:
    """
    Reemplaza correos, tarjetas de crédito, claves de API y contraseñas por marcadores redactados.
    """
    if not text:
        return text

    # Redactar contraseñas asignadas
    sanitized = PASSWORD_ASSIGNMENT_PATTERN.sub(r"\1\2[REDACTED_SECRET]", text)
    # Redactar claves de API
    sanitized = API_KEY_PATTERN.sub("[REDACTED_SECRET]", sanitized)
    # Redactar números de tarjeta de crédito
    sanitized = CREDIT_CARD_PATTERN.sub("[REDACTED_CARD]", sanitized)
    # Redactar correos electrónicos
    sanitized = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", sanitized)

    return sanitized
