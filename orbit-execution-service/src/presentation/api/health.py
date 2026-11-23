import asyncio
import logging

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from src.infrastructure.adapters.event_publisher import RabbitMQEventPublisher

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

CHECK_TIMEOUT_SECONDS = 2.0


async def _check_mysql(engine: AsyncEngine) -> bool:
    try:
        async with asyncio.timeout(CHECK_TIMEOUT_SECONDS):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.warning("MySQL readiness check failed", exc_info=True)
        return False


def _check_rabbitmq(publisher: RabbitMQEventPublisher) -> bool:
    if publisher.is_connected:
        return True
    logger.warning("RabbitMQ readiness check failed: connection closed")
    return False


@router.get(
    "/health",
    summary="Liveness probe",
    description="Report that the process is up and serving requests.",
)
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description="Report whether the service dependencies are reachable.",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "A dependency is unavailable"
        },
    },
)
async def readiness(request: Request) -> JSONResponse:
    checks = {
        "mysql": await _check_mysql(request.app.state.engine),
        "rabbitmq": _check_rabbitmq(request.app.state.publisher),
    }
    ready = all(checks.values())
    return JSONResponse(
        status_code=(
            status.HTTP_200_OK
            if ready
            else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content={
            "status": "ok" if ready else "unavailable",
            "checks": {
                name: "ok" if ok else "fail" for name, ok in checks.items()
            },
        },
    )
