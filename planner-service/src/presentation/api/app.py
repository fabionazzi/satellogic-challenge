from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from src.infrastructure.external.orbit_execution_engine import (
    HTTPOrbitExecutionService,
)
from src.infrastructure.persistence.sql.database import (
    build_engine,
    build_sessionmaker,
)
from src.presentation.api.v1.router import router as v1_router
from src.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = build_engine(settings)
    app.state.sessionmaker = build_sessionmaker(engine)
    client = httpx.AsyncClient(
        base_url=settings.base_orbit_execution_url,
        timeout=httpx.Timeout(5.0),
    )
    app.state.orbit_service = HTTPOrbitExecutionService(client)
    yield
    await client.aclose()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Planner Service", lifespan=lifespan)
    app.include_router(v1_router, prefix="/api/v1")
    return app
