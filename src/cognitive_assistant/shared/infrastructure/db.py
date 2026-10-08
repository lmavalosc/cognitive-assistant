import logging
from typing import AsyncGenerator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from cognitive_assistant.settings import settings
from cognitive_assistant.shared.infrastructure.models import Base

logger = logging.getLogger(__name__)

_async_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_async_engine() -> AsyncEngine:
    """Devuelve el motor SQLAlchemy 2.0 Async configurado."""
    global _async_engine
    if _async_engine is None:
        db_url = settings.async_postgres_url
        logger.info("Inicializando AsyncEngine con URL: %s@%s:%s/%s", 
                    settings.postgres_user, settings.postgres_host, settings.postgres_port, settings.postgres_db)
        _async_engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args={"timeout": 5},
        )
    return _async_engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Devuelve el sessionmaker asíncrono."""
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_async_engine()
        _async_session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Generador de sesión asíncrona para inyección de dependencias en FastAPI."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db_schema() -> bool:
    """
    Inicializa el esquema de la base de datos creando las tablas declaradas si no existen.
    Habilita de forma idempotente la extensión 'vector' si está soportada.
    """
    engine = get_async_engine()
    try:
        async with engine.begin() as conn:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                logger.info("Extensión 'vector' verificada en PostgreSQL.")
            except Exception as ext_err:
                logger.warning("No se pudo registrar la extensión 'vector': %s", ext_err)

            await conn.run_sync(Base.metadata.create_all)
            logger.info("Esquema de base de datos inicializado exitosamente (audit_transactions).")
            return True
    except Exception as exc:
        logger.error("Error al inicializar el esquema de base de datos: %s", exc)
        return False


async def check_db_health() -> bool:
    """Verifica si la base de datos relacional y vectorial responde."""
    try:
        engine = get_async_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as exc:
        logger.debug("Comprobación de salud de PostgreSQL fallida: %s", exc)
        return False
