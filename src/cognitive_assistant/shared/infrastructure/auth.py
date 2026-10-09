"""Infraestructura de Autenticación y Autorización de Perímetro (Capa 3 / Plano B).

Implementa verificación de API Keys con tiempo constante (hmac.compare_digest),
aislamiento de identidad (Principal) y validación estricta de entorno.
"""

import hashlib
import hmac
from typing import Optional
from fastapi import Header, HTTPException, status
from pydantic import BaseModel

from cognitive_assistant.settings import settings
from cognitive_assistant.shared.telemetry.logging import get_logger

logger = get_logger("cognitive_assistant.infrastructure.auth")


class Principal(BaseModel):
    """Representa la identidad del llamante autenticado."""

    user_id: str
    api_key: str


def derive_user_id_from_key(api_key: str) -> str:
    """Deriva un identificador de usuario determinista a partir de la API Key."""
    # Si la clave contiene un identificador amigable antes de un guión o guión bajo
    for sep in ("-", "_"):
        if sep in api_key:
            prefix = api_key.split(sep)[0].strip()
            if prefix and len(prefix) >= 3 and prefix.isalnum():
                return f"user_{prefix}"

    # Hash SHA-256 corto determinista
    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:10]
    return f"usr_{digest}"


async def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Principal:
    """
    Dependencia FastAPI que valida la presencia y autenticidad del header X-API-Key.
    
    Reglas:
    1. Si app_env != 'local': X-API-Key es estrictamente obligatorio. Fallar con 401 si falta o es inválido.
    2. Si app_env == 'local':
       - Si X-API-Key es provisto: se valida contra settings.api_keys si están configuradas. Si es inválido, 401.
       - Si X-API-Key no es provisto: se permite acceso en modo desarrollo con identidad default.
    """
    configured_keys = settings.api_keys
    is_local = settings.app_env == "local"

    # Caso 1: En entorno no local, el header es obligatorio
    if not is_local:
        if not x_api_key:
            logger.warning("Acceso denegado: Header X-API-Key ausente en entorno no local (%s)", settings.app_env)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autenticación requerida: Header 'X-API-Key' ausente.",
            )

        # Comparación en tiempo constante contra las claves configuradas
        matched = any(hmac.compare_digest(x_api_key, valid_key) for valid_key in configured_keys)
        if not matched:
            logger.warning("Acceso denegado: API Key no autorizada en entorno %s", settings.app_env)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credencial no válida: API Key no autorizada.",
            )

        user_id = derive_user_id_from_key(x_api_key)
        return Principal(user_id=user_id, api_key=x_api_key)

    # Caso 2: Entorno local
    if x_api_key:
        if configured_keys:
            matched = any(hmac.compare_digest(x_api_key, valid_key) for valid_key in configured_keys)
            if not matched:
                logger.warning("Acceso denegado en local: API Key no coincide con claves autorizadas.")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credencial no válida: API Key no autorizada.",
                )
        user_id = derive_user_id_from_key(x_api_key)
        return Principal(user_id=user_id, api_key=x_api_key)

    # Modo desarrollo local sin header: identidad default
    return Principal(user_id="default_user", api_key="local-dev")
