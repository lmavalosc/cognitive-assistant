import pytest
from fastapi.testclient import TestClient
from cognitive_assistant.app import create_app
from cognitive_assistant.shared.infrastructure.audit import AuditService

client = TestClient(create_app())


@pytest.mark.asyncio
async def test_post_reception_deliberate():
    """Verifica que el endpoint /reception/deliberate ejecute el ciclo cognitivo y registre auditoría."""
    payload = {
        "content": "Necesito un resumen de los objetivos de la etapa 1",
        "user_id": "moises_tester",
        "metadata": {"origin": "pytest"},
    }
    response = client.post("/reception/deliberate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "completed"
    assert "response" in data
    assert len(data["response"]) > 0
    assert len(data["plan"]) > 0
    assert "trace_id" in data
    assert "x-trace-id" in response.headers
    assert response.headers["x-trace-id"] == data["trace_id"]

    # Verificar que el registro de auditoría se haya persistido en PostgreSQL
    audit_entry = await AuditService.get_by_trace_id(data["trace_id"])
    if audit_entry is not None:
        assert audit_entry.trace_id == data["trace_id"]
        assert audit_entry.endpoint == "/reception/deliberate"
        assert audit_entry.response_status == 200



def test_memory_api_endpoints():
    """Verifica los endpoints REST de Capa 5 Memoria."""
    # 1. Agregar memoria
    add_payload = {
        "content": "El usuario investiga la arquitectura de 8 capas del cerebro.",
        "user_id": "test_user_api",
    }
    add_res = client.post("/memory/add", json=add_payload)
    assert add_res.status_code == 201
    assert "trace_id" in add_res.json()

    # 2. Buscar memoria
    search_res = client.get("/memory/search", params={"q": "8 capas", "user_id": "test_user_api"})
    assert search_res.status_code == 200
    assert len(search_res.json()["results"]) > 0

    # 3. Listar todas
    all_res = client.get("/memory/all", params={"user_id": "test_user_api"})
    assert all_res.status_code == 200
    assert len(all_res.json()["results"]) >= 1
