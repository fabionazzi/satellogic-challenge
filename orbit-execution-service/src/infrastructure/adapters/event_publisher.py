import json
import logging
from typing import Self

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message
from aio_pika.abc import AbstractExchange, AbstractRobustConnection
from src.application.events import SimulationEvent
from src.application.ports.event_publisher import EventPublisher
from src.settings import Settings

logger = logging.getLogger(__name__)


QUEUE_ARGS = {
    "x-queue-type": "quorum",
    "x-single-active-consumer": True,
    "x-delivery-limit": 5,
}


class RabbitMQEventPublisher(EventPublisher):
    """RabbitMQ event publisher"""

    def __init__(
        self,
        connection: AbstractRobustConnection,
        exchange: AbstractExchange,
        publish_timeout: float,
    ) -> None:
        self._connection = connection
        self._exchange = exchange
        self._publish_timeout = publish_timeout

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
            channel = await connection.channel(
                publisher_confirms=True,
                on_return_raises=True,
            )
            exchange = await channel.declare_exchange(
                settings.rabbitmq_exchange, ExchangeType.TOPIC, durable=True
            )
        except Exception:
            await connection.close()
            raise
        return cls(
            connection, exchange, settings.rabbitmq_publish_timeout_seconds
        )

    async def publish(self, event: SimulationEvent) -> None:
        body = json.dumps(
            {**event.payload, "occurred_at": event.occurred_at.isoformat()}
        ).encode()
        await self._exchange.publish(
            Message(
                body=body,
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT,
                type=event.name,
                timestamp=event.occurred_at,
            ),
            routing_key=event.name,
            mandatory=True,
            timeout=self._publish_timeout,
        )

    async def close(self) -> None:
        await self._connection.close()
