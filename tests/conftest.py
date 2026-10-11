from unittest.mock import AsyncMock, patch
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from cognitive_assistant.app import create_app
from cognitive_assistant.shared.infrastructure.db import dispose_db_engine
from cognitive_assistant.shared.infrastructure.redis_client import close_redis_client


@pytest.fixture(autouse=True)
def mock_db_init_for_tests(monkeypatch):
    """Evita esperas de timeout al inicializar esquemas o rate limit en entornos sin servicios activos."""
    monkeypatch.setattr("cognitive_assistant.settings.settings.rate_limit_enabled", False)
    with patch("cognitive_assistant.app.init_db_schema", new_callable=AsyncMock) as m:
        m.return_value = True
        yield


@pytest.fixture
def client():
    """Proporciona un TestClient con ciclo de vida completo (lifespan) garantizado para pruebas síncronas."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client():
    """Proporciona un AsyncClient (HTTPX) ejecutado en el mismo event loop de las pruebas asíncronas."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def cleanup_async_resources():
    """Garantiza la liberación y cierre limpio de recursos asíncronos por cada test."""
    yield
    await close_redis_client()
    await dispose_db_engine()
