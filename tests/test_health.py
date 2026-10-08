from fastapi.testclient import TestClient
from cognitive_assistant.app import create_app

client = TestClient(create_app())


def test_health_check_returns_200_and_ok_status():
    """Verifica que GET /health responda 200 con la estructura del núcleo."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "cognitive-assistant"
    assert data["environment"] == "local"
    assert data["version"] == "0.1.0"


def test_health_check_trace_id_in_header():
    """Verifica que la respuesta de /health incluya la cabecera X-Trace-ID."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-trace-id" in response.headers
    assert len(response.headers["x-trace-id"]) > 0
