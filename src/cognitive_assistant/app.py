from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from cognitive_assistant import __version__
from cognitive_assistant.modules.c2_reception.router import router as reception_router
from cognitive_assistant.settings import Settings, get_settings
from cognitive_assistant.shared.telemetry.logging import get_logger, setup_logging
from cognitive_assistant.shared.telemetry.trace import TraceMiddleware, get_trace_id


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Ciclo de vida de la aplicación FastAPI."""
    settings = get_settings()
    setup_logging(settings.log_level)
    logger = get_logger("cognitive_assistant.lifecycle")
    logger.info("Iniciando %s v%s [env=%s]", settings.app_name, __version__, settings.app_env)
    yield
    logger.info("Deteniendo %s...", settings.app_name)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Fábrica de la aplicación FastAPI."""
    cfg = settings or get_settings()

    app = FastAPI(
        title=cfg.app_name,
        version=__version__,
        description="Tronco Encefálico del Asistente Cognitivo - Núcleo Transaccional Mínimo (Etapa 1).",
        lifespan=lifespan,
    )

    # Middleware de Trazabilidad (primero para capturar todo el ciclo de vida de la petición)
    app.add_middleware(TraceMiddleware)

    # Enrutadores
    app.include_router(reception_router)

    @app.get("/", tags=["Root"], summary="Información del Núcleo")
    async def root():
        return {
            "name": cfg.app_name,
            "version": __version__,
            "status": "online",
            "trace_id": get_trace_id(),
            "docs_url": "/docs",
        }

    return app
