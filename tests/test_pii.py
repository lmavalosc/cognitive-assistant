import pytest
import uuid
from cognitive_assistant.shared.infrastructure.audit import AuditService
from cognitive_assistant.shared.infrastructure.pii import scrub_pii


def test_scrub_pii_redacts_credentials_and_personal_data():
    """Verifica que scrub_pii enmascare tarjetas, correos, secretos y contraseñas."""
    raw_text = (
        "El cliente juan.perez@empresa.org con tarjeta 4111 2222 3333 4444 "
        "usó la clave sk-secretkey1234567890abcdef y password=miclavesecreta para autenticarse."
    )
    cleaned = scrub_pii(raw_text)

    assert "juan.perez@empresa.org" not in cleaned
    assert "[REDACTED_EMAIL]" in cleaned

    assert "4111 2222 3333 4444" not in cleaned
    assert "[REDACTED_CARD]" in cleaned

    assert "sk-secretkey1234567890abcdef" not in cleaned
    assert "[REDACTED_SECRET]" in cleaned

    assert "miclavesecreta" not in cleaned


@pytest.mark.asyncio
async def test_audit_persists_scrubbed_summary():
    """Verifica que AuditService almacene en PostgreSQL el resumen ofuscado sin datos PII en claro."""
    test_trace = f"pii-trace-{uuid.uuid4().hex[:8]}"
    summary_with_pii = "Usuario reporta pago con tarjeta 5500 0000 0000 1234 desde contacto@seguro.com"

    await AuditService.record_transaction(
        trace_id=test_trace,
        endpoint="/test/pii",
        summary=summary_with_pii,
    )

    record = await AuditService.get_by_trace_id(test_trace)
    assert record is not None
    assert "5500 0000 0000 1234" not in record.request_summary
    assert "contacto@seguro.com" not in record.request_summary
    assert "[REDACTED_CARD]" in record.request_summary
    assert "[REDACTED_EMAIL]" in record.request_summary
