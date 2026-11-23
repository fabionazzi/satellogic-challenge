import asyncio
import logging
import signal

from src.application.ports.event_consumer import SimulationEventConsumer
from src.application.unit_of_work import CaptureUOW
from src.application.use_cases.simulation import ProcessSimulationEventUseCase
from src.domain.exceptions import StatusTransitionError
from src.infrastructure.messaging.rabbitmq_consumer import (
    RabbitMQEventConsumer,
)
from src.infrastructure.persistence.sql.database import (
    build_engine,
    build_sessionmaker,
)
from src.infrastructure.persistence.sql.unit_of_work import (
    SQLCaptureUnitOfWork,
)
from src.settings import get_settings

logger = logging.getLogger(__name__)


async def run(
    consumer: SimulationEventConsumer,
    use_case: ProcessSimulationEventUseCase,
) -> None:
    while True:
        event = await consumer.read()
        try:
            await use_case.execute(event)
        except StatusTransitionError:
            logger.warning("Skipping %s: invalid transition", event.name)
            await consumer.ack()
        except Exception:
            logger.exception("Failed to handle %s", event.name)
            await consumer.reject(requeue=True)
        else:
            await consumer.ack()


async def main() -> None:
    settings = get_settings()
    engine = build_engine(settings)
    sessionmaker = build_sessionmaker(engine)

    def uow_factory() -> CaptureUOW:
        return SQLCaptureUnitOfWork(sessionmaker)

    use_case = ProcessSimulationEventUseCase(uow_factory)
    consumer = await RabbitMQEventConsumer.connect(settings)
    task = asyncio.create_task(run(consumer, use_case))

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, task.cancel)

    logger.info("Worker started")
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Worker stopping")
    finally:
        await consumer.close()
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(main())
