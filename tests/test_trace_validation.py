import pytest
import re


@pytest.mark.asyncio
async def test_malicious_trace_id_is_regenerated(async_client):
    """
    Criterio de Aceptación:
    Header X-Trace-ID con inyección o caracteres no permitidos es rechazado y regenerado con UUID4 limpio.
    """
    malicious_trace = "postgres'; DROP TABLE audit_transactions; --"
    response = await async_client.get("/health", headers={"X-Trace-ID": malicious_trace})

    assert response.status_code == 200
    returned_trace = response.headers.get("X-Trace-ID")

    assert returned_trace is not None
    assert returned_trace != malicious_trace
    # Debe ser un UUID válido (36 caracteres con guiones)
    uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
    assert uuid_pattern.match(returned_trace)


@pytest.mark.asyncio
async def test_valid_custom_trace_id_is_preserved(async_client):
    """Un X-Trace-ID seguro y alfanumérico es preservado íntegramente."""
    valid_trace = "valid-trace-id-987654321"
    response = await async_client.get("/health", headers={"X-Trace-ID": valid_trace})

    assert response.status_code == 200
    assert response.headers.get("X-Trace-ID") == valid_trace
