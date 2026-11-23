import uvicorn
from src.presentation.api.app import create_app
from src.settings import get_settings

app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.app_host,
        port=settings.app_port,
    )
