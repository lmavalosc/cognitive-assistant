from fastapi import FastAPI
from cognitive_assistant.modules.c2_reception.router import router as reception_router
from cognitive_assistant.modules.c5_memory.router import router as memory_router
from cognitive_assistant.settings import settings
from cognitive_assistant.shared.telemetry.logging import setup_logging
from cognitive_assistant.shared.telemetry.trace import TraceIDMiddleware


def create_app() -> FastAPI:
    """Fábrica de la aplicación FastAPI para el núcleo transaccional."""
    setup_logging(settings.log_level)

    app = FastAPI(
        title="Asistente Cognitivo Modular",
        version="0.1.0",
    )

    app.add_middleware(TraceIDMiddleware)
    app.include_router(reception_router)
    app.include_router(memory_router)

    return app

