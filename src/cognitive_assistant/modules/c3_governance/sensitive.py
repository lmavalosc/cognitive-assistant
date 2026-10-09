"""Filtro de Detección de Datos Sensibles (PII, Secretos y Credenciales).

Evita la fuga o persistencia involuntaria de información crítica en memorias
semánticas o trazas externas.
"""

import re
from typing import Optional, Tuple

# Patrones para detección de secretos y PII
API_KEY_PATTERN = re.compile(
    r"\b(?:sk-[a-zA-Z0-9_\-]{20,}|ghp_[a-zA-Z0-9]{20,}|bearer\s+[a-zA-Z0-9_\-\.]{25,}|key-[a-zA-Z0-9]{20,})\b",
    re.IGNORECASE,
)
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)
CREDIT_CARD_PATTERN = re.compile(
    r"\b(?:\d{4}[ -]?){3}\d{4}\b"
)
PASSWORD_PATTERN = re.compile(
    r"(?i)\b(?:password|contrase[ñn]a|passwd|secret_token|access_token)\s*[:=]\s*\S+"
)


def contains_sensitive_data(text: str) -> Tuple[bool, Optional[str]]:
    """
    Analiza una cadena de texto para detectar secretos, credenciales o PII crítico.
    
    Retorna:
        Tuple[bool, Optional[str]]: (es_sensible, motivo_o_descripcion)
    """
    if not text:
        return False, None

    if API_KEY_PATTERN.search(text):
        return True, "API Key o secreto de autenticación detectado"

    if CREDIT_CARD_PATTERN.search(text):
        return True, "Número de tarjeta de crédito detectado"

    if PASSWORD_PATTERN.search(text):
        return True, "Contraseña o token en texto plano detectado"

    if EMAIL_PATTERN.search(text):
        return True, "Dirección de correo electrónico detectada"

    return False, None
