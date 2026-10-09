import pytest
from unittest.mock import patch
from cognitive_assistant.settings import settings


@pytest.mark.asyncio
async def test_rate_limit_blocks_excessive_requests(async_client):
    """Verifica que ráfagas por encima del límite configurado retornen HTTP 429 RFC 7807."""
    with patch.object(settings, "rate_limit_enabled", True):
        with patch.object(settings, "rate_limit_requests", 5):
            with patch.object(settings, "rate_limit_window_seconds", 30):
                custom_header = {"X-API-Key": "ratelimit-test-key-01"}
                statuses = []
                for i in range(7):
                    res = await async_client.post(
                        "/reception/message",
                        json={"content": f"Mensaje número {i}", "source": "test"},
                        headers=custom_header,
                    )
                    statuses.append(res.status_code)

                # Al menos una de las solicitudes debe ser bloqueada con HTTP 429
                assert 429 in statuses
                idx_429 = statuses.index(429)
                assert idx_429 >= 5

                # Verificar estructura RFC 7807
                res_blocked = await async_client.post(
                    "/reception/message",
                    json={"content": "Mensaje bloqueado", "source": "test"},
                    headers=custom_header,
                )
                assert res_blocked.status_code == 429
                data = res_blocked.json()
                assert data["status"] == 429
                assert data["type"] == "urn:cognitive-assistant:error:rate-limit-exceeded"
                assert "retry-after" in res_blocked.headers


@pytest.mark.asyncio
async def test_rate_limit_excludes_health_check(async_client):
    """Verifica que el endpoint /health esté excluido de la limitación de tasa."""
    with patch.object(settings, "rate_limit_enabled", True):
        with patch.object(settings, "rate_limit_requests", 3):
            for _ in range(6):
                res = await async_client.get("/health")
                assert res.status_code == 200
