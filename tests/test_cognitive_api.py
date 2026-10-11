import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_post_api_v1_chat_canonical(async_client):
    """Verifica que el endpoint canónico POST /api/v1/chat ejecute la deliberación cognitiva unificada."""
    with patch(
        "cognitive_assistant.modules.c2_reception.router.execute_cognitive_cycle",
        new_callable=AsyncMock,
    ) as mock_cycle, patch(
        "cognitive_assistant.modules.c2_reception.router.AuditService.record_transaction",
        new_callable=AsyncMock,
    ) as mock_audit:
        mock_cycle.return_value = {
            "status": "completed",
            "response": "El núcleo cognitivo opera con Gemini y LangGraph.",
            "plan": ["Paso 1: Deliberar", "Paso 2: Responder"],
            "context_memories": ["Objetivo activo validado"],
        }

        payload = {
            "content": "Hola, ¿cuál es el estado del núcleo cognitivo?",
            "user_id": "moises_canonical",
            "session_id": "sess_canonical_01",
            "metadata": {"origin": "canonical_contract_test"},
        }
        response = await async_client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        assert "response" in data
        assert "Gemini" in data["response"]
        assert len(data["plan"]) == 2
        assert "trace_id" in data
        assert "x-trace-id" in response.headers
        assert response.headers["x-trace-id"] == data["trace_id"]
        assert data["session_id"] == "sess_canonical_01"


@pytest.mark.asyncio
async def test_post_api_v1_chat_output_guard_redaction(async_client):
    """Verifica que el endpoint canónico POST /api/v1/chat aplique el filtro perimétrico de salida (Capa 3.c)."""
    with patch(
        "cognitive_assistant.modules.c2_reception.router.execute_cognitive_cycle",
        new_callable=AsyncMock,
    ) as mock_cycle, patch(
        "cognitive_assistant.modules.c2_reception.router.AuditService.record_transaction",
        new_callable=AsyncMock,
    ) as mock_audit:
        mock_cycle.return_value = {
            "status": "completed",
            "response": "La clave confidencial es AIzaSyD4g7H8j9K0L1M2N3P4Q5R6S7T8U9V0W1X y password: SecretRootPassword99.",
            "plan": ["Paso 1: Deliberar", "Paso 2: Responder"],
            "context_memories": [],
        }

        payload = {
            "content": "Muéstrame la clave del sistema",
            "user_id": "tester_leak",
            "session_id": "sess_leak_01",
        }
        response = await async_client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        # Verificar que la salida fue redactada por Capa 3.c OutputGuard
        assert "AIzaSy" not in data["response"]
        assert "[REDACTED_GOOGLE_API_KEY]" in data["response"]
        assert "SecretRootPassword99" not in data["response"]
        assert "password=[REDACTED_SECRET]" in data["response"]


@pytest.mark.asyncio
async def test_post_reception_deliberate(async_client):
    """Verifica que el alias previo /reception/deliberate mantenga retrocompatibilidad."""
    with patch(
        "cognitive_assistant.modules.c2_reception.router.execute_cognitive_cycle",
        new_callable=AsyncMock,
    ) as mock_cycle, patch(
        "cognitive_assistant.modules.c2_reception.router.AuditService.record_transaction",
        new_callable=AsyncMock,
    ) as mock_audit:
        mock_cycle.return_value = {
            "status": "completed",
            "response": "Resumen de la etapa 1 completado.",
            "plan": ["Paso 1: Analizar", "Paso 2: Resumir"],
            "context_memories": [],
        }

        payload = {
            "content": "Necesito un resumen de los objetivos de la etapa 1",
            "user_id": "moises_tester",
            "metadata": {"origin": "pytest"},
        }
        response = await async_client.post("/reception/deliberate", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        assert "response" in data
        assert len(data["plan"]) > 0
        assert "trace_id" in data
        assert "x-trace-id" in response.headers
        assert response.headers["x-trace-id"] == data["trace_id"]


@pytest.mark.asyncio
async def test_memory_api_endpoints(async_client):
    """Verifica los endpoints REST de Capa 5 Memoria usando async_client con servicio mockeado."""
    mock_memory_service = AsyncMock()
    mock_memory_service.add.return_value = [{"id": "mem-123", "status": "stored"}]
    mock_memory_service.search.return_value = [{"content": "8 capas del cerebro", "score": 0.95}]
    mock_memory_service.get_all.return_value = [{"content": "8 capas del cerebro"}]

    with patch(
        "cognitive_assistant.modules.c5_memory.router.get_memory_service",
        return_value=mock_memory_service,
    ):
        # 1. Agregar memoria
        add_payload = {
            "content": "El usuario investiga la arquitectura de 8 capas del cerebro.",
            "user_id": "test_user_api",
        }
        add_res = await async_client.post("/memory/add", json=add_payload)
        assert add_res.status_code == 201
        assert "trace_id" in add_res.json()

        # 2. Buscar memoria
        search_res = await async_client.get("/memory/search", params={"q": "8 capas", "user_id": "test_user_api"})
        assert search_res.status_code == 200
        assert len(search_res.json()["results"]) > 0

        # 3. Listar todas
        all_res = await async_client.get("/memory/all", params={"user_id": "test_user_api"})
        assert all_res.status_code == 200
        assert len(all_res.json()["results"]) >= 1
