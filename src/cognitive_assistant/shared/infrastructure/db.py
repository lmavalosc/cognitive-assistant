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

import asyncio
logger = logging.getLogger(__name__)

_async_engine: Optional[AsyncEngine] = None
_async_engine_loop: Optional[asyncio.AbstractEventLoop] = None
_async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_async_engine() -> AsyncEngine:
    """Devuelve el motor SQLAlchemy 2.0 Async configurado, adaptándose al event loop activo."""
    global _async_engine, _async_engine_loop, _async_session_factory
    current_loop = None
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        pass

    # Si el motor previo fue creado en un event loop distinto, descartar para evitar conexiones huérfanas
    if _async_engine is not None and _async_engine_loop is not None and current_loop is not None and _async_engine_loop != current_loop:
        _async_engine = None
        _async_session_factory = None

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
        _async_engine_loop = current_loop
    return _async_engine


async def dispose_db_engine() -> None:
    """Cierra y libera limpiamente el motor y el pool de conexiones asyncpg."""
    global _async_engine, _async_session_factory, _async_engine_loop
    if _async_engine is not None:
        try:
            await _async_engine.dispose()
        except Exception as exc:
            logger.debug("Error al liberar AsyncEngine: %s", exc)
        finally:
            _async_engine = None
            _async_session_factory = None
            _async_engine_loop = None


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
