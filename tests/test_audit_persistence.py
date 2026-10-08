import pytest
import uuid
from cognitive_assistant.shared.infrastructure.db import init_db_schema, check_db_health
from cognitive_assistant.shared.infrastructure.audit import AuditService


@pytest.mark.asyncio
async def test_audit_table_initialization_and_persistence():
    """Verifica que el esquema se inicialice y las transacciones se persistan en PostgreSQL."""
    is_healthy = await check_db_health()
    assert is_healthy is True

    init_ok = await init_db_schema()
    assert init_ok is True

    sample_trace_id = f"test-trace-{uuid.uuid4().hex[:8]}"
    sample_session_id = "session-test-audit"

    # Registrar transacción
    tx = await AuditService.record_transaction(
        trace_id=sample_trace_id,
        endpoint="/api/v1/chat",
        channel="http",
        status=200,
        duration_ms=12.5,
        summary="Test prompt transaction",
        session_id=sample_session_id,
        metadata={"model": "gpt-4o-mini", "tokens": 42},
        security_violation=False,
    )
    assert tx is not None
    assert tx.trace_id == sample_trace_id
    assert tx.response_status == 200
    assert tx.duration_ms == 12.5

    # Recuperar por trace_id
    recovered = await AuditService.get_by_trace_id(sample_trace_id)
    assert recovered is not None
    assert recovered.trace_id == sample_trace_id
    assert recovered.session_id == sample_session_id
    assert recovered.metadata_json == {"model": "gpt-4o-mini", "tokens": 42}

    # Listar recientes
    recent = await AuditService.get_recent_transactions(limit=10)
    assert len(recent) >= 1
    assert any(t.trace_id == sample_trace_id for t in recent)
