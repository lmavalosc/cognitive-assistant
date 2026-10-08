from fastapi.testclient import TestClient
from cognitive_assistant.app import create_app

client = TestClient(create_app())


def test_health_check_returns_200_and_ok_status():
    """Verifica que GET /health responda 200 con estructura esperada."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "version" in data
    assert "trace_id" in data
    assert len(data["trace_id"]) > 0


def test_health_check_trace_id_matches_header():
    """Verifica que el trace_id en el cuerpo coincida con el header X-Trace-ID."""
    response = client.get("/health")
    assert response.status_code == 200

    header_trace = response.headers.get("x-trace-id")
    body_trace = response.json().get("trace_id")

    assert header_trace is not None
    assert body_trace is not None
    assert header_trace == body_trace


def test_root_endpoint_returns_200():
    """Verifica que GET / responde 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
