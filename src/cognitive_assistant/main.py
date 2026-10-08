import uvicorn
from cognitive_assistant.app import create_app
from cognitive_assistant.settings import settings

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "cognitive_assistant.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
