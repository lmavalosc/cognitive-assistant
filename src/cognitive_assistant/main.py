import uvicorn
from cognitive_assistant.app import create_app
from cognitive_assistant.settings import get_settings

app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "cognitive_assistant.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
