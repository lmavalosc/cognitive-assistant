import logging
from fastapi.testclient import TestClient
from cognitive_assistant.app import create_app
from cognitive_assistant.shared.telemetry.logging import TraceIdFilter
from cognitive_assistant.shared.telemetry.trace import (
    generate_trace_id,
    get_trace_id,
    reset_trace_id,
    set_trace_id,
)

client = TestClient(create_app())


def test_unique_trace_id_per_request():
    """Cada request sin header previo debe generar un trace_id único."""
    response_1 = client.get("/health")
    response_2 = client.get("/health")

    trace_1 = response_1.headers.get("x-trace-id")
    trace_2 = response_2.headers.get("x-trace-id")

    assert trace_1 is not None
    assert trace_2 is not None
    assert trace_1 != trace_2


def test_propagates_custom_trace_id():
    """Si el cliente envía un X-Trace-ID existente, debe respetarse y propagarse."""
    custom_trace = "custom-trace-uuid-12345"
    response = client.get("/health", headers={"X-Trace-ID": custom_trace})

    assert response.status_code == 200
    assert response.headers.get("x-trace-id") == custom_trace
    assert response.json()["trace_id"] == custom_trace


def test_trace_id_in_log_record():
    """Verifica que el TraceIdFilter inyecte el trace_id actual en los registros de logging."""
    test_id = generate_trace_id()
    token = set_trace_id(test_id)

    try:
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="Mensaje de prueba",
            args=(),
            exc_info=None,
        )
        filter_instance = TraceIdFilter()
        filter_instance.filter(record)

        assert hasattr(record, "trace_id")
        assert record.trace_id == test_id
    finally:
        reset_trace_id(token)


def test_reception_message_trace_propagation():
    """Verifica la trazabilidad en la ruta de recepción y despacho C2 -> C8."""
    custom_trace = "reception-trace-777"
    response = client.post(
        "/reception/message",
        json={"content": "Mensaje transaccional de prueba", "source": "unit_test"},
        headers={"X-Trace-ID": custom_trace},
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert data["trace_id"] == custom_trace
    assert data["dispatched"] is True
    assert response.headers.get("x-trace-id") == custom_trace
