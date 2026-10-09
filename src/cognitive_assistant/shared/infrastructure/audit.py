import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select

from cognitive_assistant.shared.infrastructure.db import get_session_factory
from cognitive_assistant.shared.infrastructure.models import AuditTransaction
from cognitive_assistant.shared.infrastructure.pii import scrub_pii

logger = logging.getLogger(__name__)


class AuditService:
    """
    Servicio de Auditoría Transaccional para el Plano B.
    Garantiza persistencia inmutable y resiliente de cada interacción.
    """

    @staticmethod
    async def record_transaction(
        trace_id: str,
        endpoint: str,
        channel: str = "http",
        status: int = 200,
        duration_ms: Optional[float] = None,
        summary: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        security_violation: bool = False,
        violation_reason: Optional[str] = None,
    ) -> Optional[AuditTransaction]:
        """
        Registra una transacción en la tabla audit_transactions.
        Si la base de datos no está disponible, realiza fallback a logging sin fallar.
        Aplica ofuscación de PII previa a la persistencia.
        """
        clean_summary = scrub_pii(summary[:1000]) if summary else None
        record = AuditTransaction(
            trace_id=trace_id,
            session_id=session_id,
            channel=channel,
            endpoint=endpoint,
            request_summary=clean_summary,
            response_status=status,
            duration_ms=duration_ms,
            metadata_json=metadata,
            security_violation=security_violation,
            violation_reason=violation_reason,
        )


        try:
            factory = get_session_factory()
            async with factory() as session:
                session.add(record)
                await session.commit()
                await session.refresh(record)
                logger.info(
                    "Transacción registrada exitosamente en DB: trace_id=%s, endpoint=%s, status=%d",
                    trace_id, endpoint, status
                )
                return record
        except Exception as exc:
            logger.warning(
                "Fallo al persistir transacción en PostgreSQL (trace_id=%s): %s. Fallback a log.",
                trace_id, exc
            )
            return None

    @staticmethod
    async def get_by_trace_id(trace_id: str) -> Optional[AuditTransaction]:
        """Recupera el registro de auditoría asociado a un trace_id."""
        try:
            factory = get_session_factory()
            async with factory() as session:
                stmt = select(AuditTransaction).where(AuditTransaction.trace_id == trace_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception as exc:
            logger.error("Error al consultar auditoría por trace_id=%s: %s", trace_id, exc)
            return None

    @staticmethod
    async def get_recent_transactions(limit: int = 20) -> List[AuditTransaction]:
        """Recupera las transacciones más recientes ordenadas cronológicamente."""
        try:
            factory = get_session_factory()
            async with factory() as session:
                stmt = select(AuditTransaction).order_by(desc(AuditTransaction.created_at)).limit(limit)
                result = await session.execute(stmt)
                return list(result.scalars().all())
        except Exception as exc:
            logger.error("Error al listar transacciones recientes: %s", exc)
            return []
