from fastapi.testclient import TestClient
from cognitive_assistant.app import create_app

client = TestClient(create_app())


def test_post_reception_deliberate():
    """Verifica que el endpoint /reception/deliberate ejecute el ciclo cognitivo."""
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
