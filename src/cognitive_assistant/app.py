from contextlib import asynccontextmanager
from fastapi import FastAPI
from cognitive_assistant.modules.c2_reception.router import router as reception_router
from cognitive_assistant.modules.c5_memory.router import router as memory_router
from cognitive_assistant.settings import settings
from cognitive_assistant.shared.infrastructure.db import init_db_schema, dispose_db_engine
from cognitive_assistant.shared.infrastructure.redis_client import close_redis_client
from cognitive_assistant.shared.telemetry.logging import setup_logging
from cognitive_assistant.shared.telemetry.trace import TraceIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación: inicializa esquemas y libera conexiones al apagar."""
    await init_db_schema()
    try:
        yield
    finally:
        await dispose_db_engine()
        await close_redis_client()


def create_app() -> FastAPI:
    """Fábrica de la aplicación FastAPI para el núcleo transaccional."""
    setup_logging(settings.log_level)

    app = FastAPI(
        title="Asistente Cognitivo Modular",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(TraceIDMiddleware)
    app.include_router(reception_router)
    app.include_router(memory_router)

    return app


