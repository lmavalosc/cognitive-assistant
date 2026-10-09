import pytest
from unittest.mock import patch
from fastapi import HTTPException
from cognitive_assistant.settings import settings
from cognitive_assistant.shared.infrastructure.auth import Principal, require_api_key


@pytest.mark.asyncio
async def test_auth_local_mode_without_header():
    """En entorno local, la ausencia del header X-API-Key otorga identidad por defecto."""
    principal = await require_api_key(x_api_key=None)
    assert principal.user_id == "default_user"
    assert principal.api_key == "local-dev"


@pytest.mark.asyncio
async def test_auth_with_valid_key():
    """Valida que una API key conocida derive correctamente la identidad."""
    with patch.object(settings, "api_keys", ["secret-key-user1", "secret-key-user2"]):
        principal = await require_api_key(x_api_key="secret-key-user1")
        assert principal.api_key == "secret-key-user1"
        assert principal.user_id.startswith("user_") or principal.user_id.startswith("usr_")


@pytest.mark.asyncio
async def test_auth_with_invalid_key():
    """Valida que una API key no autorizada sea rechazada con HTTP 401."""
    with patch.object(settings, "api_keys", ["secret-key-valid"]):
        with pytest.raises(HTTPException) as exc_info:
            await require_api_key(x_api_key="invalid-unauthorized-key")
        assert exc_info.value.status_code == 401
        assert "no autorizada" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_auth_strict_in_non_local_env():
    """En entornos no locales (producción, staging), la ausencia de header rechaza con 401."""
    with patch.object(settings, "app_env", "production"):
        with patch.object(settings, "api_keys", ["prod-key-123"]):
            with pytest.raises(HTTPException) as exc_info:
                await require_api_key(x_api_key=None)
            assert exc_info.value.status_code == 401
            assert "requerida" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_memory_isolation_with_api_key(async_client):
    """
    Criterio de Aceptación:
    GET /memory/all?user_id=victima con API key de otro usuario retorna solo memorias del llamante.
    """
    # 1. Guardar memoria para user_alice
    await async_client.post(
        "/memory/add",
        json={"content": "Secreto de Alice: le gusta el café."},
        headers={"X-API-Key": "alice-secret-key-123"},
    )

    # 2. Guardar memoria para user_bob
    await async_client.post(
        "/memory/add",
        json={"content": "Secreto de Bob: le gusta el té."},
        headers={"X-API-Key": "bob-secret-key-456"},
    )

    # 3. Bob intenta acceder a las memorias de Alice pasando ?user_id=user_alice
    response = await async_client.get(
        "/memory/all",
        params={"user_id": "user_alice"},
        headers={"X-API-Key": "bob-secret-key-456"},
    )
    assert response.status_code == 200
    data = response.json()

    # Debe devolver solo las de Bob, nunca las de Alice
    assert data["user_id"] != "user_alice"
    for item in data["results"]:
        text = str(item)
        assert "Secreto de Alice" not in text
