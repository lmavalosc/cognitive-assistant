import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    """Base declarativa para modelos del Asistente Cognitivo."""
    pass


class AuditTransaction(Base):
    """
    Modelo de persistencia para el Plano B (Trazabilidad Universal y Auditoría Transaccional).
    Registra cada interacción del sistema vinculada a su trace_id inmutable.
    """
    __tablename__ = "audit_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    trace_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        index=True,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    channel: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="http",
    )
    endpoint: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    request_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    response_status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=200,
    )
    duration_ms: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    security_violation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    violation_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "channel": self.channel,
            "endpoint": self.endpoint,
            "request_summary": self.request_summary,
            "response_status": self.response_status,
            "duration_ms": self.duration_ms,
            "metadata_json": self.metadata_json,
            "security_violation": self.security_violation,
            "violation_reason": self.violation_reason,
        }
