from contextlib import asynccontextmanager

from fastapi import FastAPI
from src.application.unit_of_work import ExecutionUOW
from src.application.use_cases.run_simulation import RunSimulationUseCase
from src.infrastructure.adapters.event_publisher import RabbitMQEventPublisher
from src.infrastructure.adapters.simulation_scheduler import (
    AsyncioSimulationScheduler,
)
from src.infrastructure.persistence.sql.database import (
    build_engine,
    build_sessionmaker,
)
from src.infrastructure.persistence.sql.unit_of_work import (
    SQLExecutionUnitOfWork,
)
from src.infrastructure.persistence.yaml.constellation_repository import (
    YamlConstellationRepository,
)
from src.presentation.api.health import router as health_router
from src.presentation.api.v1.router import router as v1_router
from src.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = build_engine(settings)
    sessionmaker = build_sessionmaker(engine)

    def uow_factory() -> ExecutionUOW:
        return SQLExecutionUnitOfWork(sessionmaker())

    constellation_repository = YamlConstellationRepository(
        settings.constellation_filepath
    )
    publisher = await RabbitMQEventPublisher.connect(settings)
    scheduler = AsyncioSimulationScheduler(
        lambda: RunSimulationUseCase(
            uow_factory=uow_factory,
            publisher=publisher,
            constellation_repository=constellation_repository,
            tick_seconds=settings.simulation_tick_seconds,
        )
    )

    app.state.engine = engine
    app.state.uow_factory = uow_factory
    app.state.constellation_repository = constellation_repository
    app.state.publisher = publisher
    app.state.scheduler = scheduler

    yield

    await scheduler.shutdown()
    await publisher.close()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Orbit Execution Service", lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(v1_router, prefix="/api/v1")
    return app
