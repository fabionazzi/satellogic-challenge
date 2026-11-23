import json
import logging
from typing import Self

import aio_pika
from aio_pika import ExchangeType
from aio_pika.abc import (
    AbstractIncomingMessage,
    AbstractQueue,
    AbstractRobustConnection,
)

from src.application.events import (
    PLAN_COMPLETED,
    PLAN_IN_PROGRESS,
    PLAN_PENDING,
    TASK_ATTEMPT,
    TASK_IN_PROGRESS,
    Payload,
    PlanPayload,
    SimulationEvent,
    TaskFinishedPayload,
    TaskStartedPayload,
)
from src.application.ports.event_consumer import SimulationEventConsumer
from src.settings import Settings

logger = logging.getLogger(__name__)


PAYLOAD_TYPES: dict[str, type[Payload]] = {
    PLAN_PENDING: PlanPayload,
    PLAN_IN_PROGRESS: PlanPayload,
    PLAN_COMPLETED: PlanPayload,
    TASK_IN_PROGRESS: TaskStartedPayload,
    TASK_ATTEMPT: TaskFinishedPayload,
}

BINDING_KEYS = ("plan.*", "task.*")


class RabbitMQEventConsumer(SimulationEventConsumer):
    """RabbitMQ consumer of simulation events"""

    def __init__(
        self, connection: AbstractRobustConnection, queue: AbstractQueue
    ) -> None:
        self._connection = connection
        self._iterator = queue.iterator()
        self._current: AbstractIncomingMessage | None = None

    @classmethod
    async def connect(cls, settings: Settings) -> Self:
        connection = await aio_pika.connect_robust(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            login=settings.rabbitmq_user,
            password=settings.rabbitmq_password.get_secret_value(),
            virtualhost=settings.rabbitmq_vhost,
        )
        try:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=settings.rabbitmq_prefetch)
            exchange = await channel.declare_exchange(
                settings.rabbitmq_exchange, ExchangeType.TOPIC, durable=True
            )
            queue = await channel.declare_queue(
                settings.rabbitmq_status_queue,
                durable=True,
                arguments={
                    "x-queue-type": "quorum",
                    "x-single-active-consumer": True,
                    "x-delivery-limit": settings.rabbitmq_delivery_limit,
                },
            )
            for binding_key in BINDING_KEYS:
                await queue.bind(exchange, routing_key=binding_key)
        except Exception:
            await connection.close()
            raise
        return cls(connection, queue)

    async def read(self) -> SimulationEvent:
        if self._current is not None:
            raise RuntimeError("Previous event was not acked or rejected")

        while True:
            message = await anext(self._iterator)
            event = self._decode(message)
            if event is None:
                await message.reject(requeue=False)
                continue
            self._current = message
            return event

    async def ack(self) -> None:
        await self._take_current().ack()

    async def reject(self, requeue: bool) -> None:
        await self._take_current().reject(requeue=requeue)

    async def close(self) -> None:
        await self._iterator.close()
        await self._connection.close()

    def _take_current(self) -> AbstractIncomingMessage:
        if self._current is None:
            raise RuntimeError("No event in flight")
        message, self._current = self._current, None
        return message

    @staticmethod
    def _decode(message: AbstractIncomingMessage) -> SimulationEvent | None:
        name = message.routing_key or ""
        payload_type = PAYLOAD_TYPES.get(name)
        if payload_type is None:
            logger.warning("Discarding event with unknown name %r", name)
            return None
        try:
            body = json.loads(message.body)
            return SimulationEvent.from_message(name, body, payload_type)
        except (ValueError, KeyError, TypeError):
            logger.warning(
                "Discarding malformed %s event", name, exc_info=True
            )
            return None
