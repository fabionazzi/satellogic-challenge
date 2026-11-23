from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import ExecutionInProgressException
from src.domain.aggregates.capture import Capture, CaptureStatus
from src.domain.aggregates.plan import Plan
from src.domain.exceptions import (
    NotPersistedError,
    RequestIdAlreadyExistsError,
)
from src.domain.repositories import (
    CaptureRepository,
    PlannerLockRepository,
    PlanRepository,
)
from src.infrastructure.persistence.sql.mappers import (
    CaptureMapper,
    PlanMapper,
)
from src.infrastructure.persistence.sql.models import (
    SQLCapture,
    SQLPlan,
    SQLPlanCapture,
    SQLPlannerLock,
)

LOCK_ROW_ID = 1


class SQLCaptureRepository(CaptureRepository):
    """SQLAlchemy implementation of the capture repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, capture: Capture) -> Capture:
        model = CaptureMapper.to_new_model(capture)
        try:
            async with self._session.begin_nested():
                self._session.add(model)
        except IntegrityError as exc:
            raise RequestIdAlreadyExistsError(
                f"Capture with request_id {capture.request_id} already exists."
            ) from exc
        return CaptureMapper.to_domain(model)

    async def update(self, capture: Capture) -> Capture:
        if capture.capture_id is None:
            raise NotPersistedError(
                "Capture must be added before being updated"
            )
        model = await self._session.get(SQLCapture, capture.capture_id)
        if model is None:
            raise NotPersistedError(f"Capture {capture.capture_id} not found")
        CaptureMapper.apply(capture, model)
        await self._session.flush()
        return CaptureMapper.to_domain(model)

    async def get_by_id(self, capture_id: int) -> Capture | None:
        model = await self._session.get(SQLCapture, capture_id)
        return CaptureMapper.to_domain(model) if model else None

    async def get_by_request_id(self, request_id: str) -> Capture | None:
        stmt = select(SQLCapture).where(SQLCapture.request_id == request_id)
        model = await self._session.scalar(stmt)
        return CaptureMapper.to_domain(model) if model else None

    async def all_by_status(self, status: CaptureStatus) -> dict[str, Capture]:
        stmt = select(SQLCapture).where(SQLCapture.status == status)
        models = await self._session.scalars(stmt)
        captures = {
            capture.request_id: CaptureMapper.to_domain(capture)
            for capture in models
        }
        return captures

    async def get_by_plan_uuid(self, plan_uuid: UUID) -> list[Capture]:
        stmt = (
            select(SQLCapture)
            .join(
                SQLPlanCapture,
                SQLPlanCapture.capture_id == SQLCapture.capture_id,
            )
            .join(SQLPlan, SQLPlan.plan_id == SQLPlanCapture.plan_id)
            .where(SQLPlan.plan_uuid == plan_uuid)
        )

        result = await self._session.execute(stmt)
        captures = result.scalars().all()
        return [CaptureMapper.to_domain(capture) for capture in captures]

    async def update_many(self, captures: list[Capture]) -> list[Capture]:
        if not captures:
            return []
        ids = [capture.capture_id for capture in captures]
        if None in ids:
            raise NotPersistedError(
                "Captures must be added before being updated"
            )
        stmt = select(SQLCapture).where(SQLCapture.capture_id.in_(ids))
        models = {m.capture_id: m for m in await self._session.scalars(stmt)}
        missing = set(ids) - models.keys()
        if missing:
            raise NotPersistedError(f"Captures {sorted(missing)} not found")
        for capture in captures:
            CaptureMapper.apply(capture, models[capture.capture_id])
        await self._session.flush()
        return [CaptureMapper.to_domain(models[i]) for i in ids]


class SQLPlanRepository(PlanRepository):
    """SQLAlchemy implementation of the plan repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, plan: Plan) -> Plan:
        model = PlanMapper.to_new_model(plan)
        self._session.add(model)
        await self._session.flush()
        return PlanMapper.to_domain(model)

    async def get_by_uuid(self, plan_uuid: UUID) -> Plan | None:
        stmt = select(SQLPlan).where(SQLPlan.plan_uuid == plan_uuid)
        model = await self._session.scalar(stmt)
        return PlanMapper.to_domain(model) if model else None

    async def update(self, plan: Plan) -> Plan:
        if plan.plan_id is None:
            raise NotPersistedError("Plan must be added before being updated")
        model = await self._session.get(SQLPlan, plan.plan_id)
        if model is None:
            raise NotPersistedError(f"Plan {plan.plan_id} not found")
        PlanMapper.apply(plan, model)
        await self._session.flush()
        return PlanMapper.to_domain(model)


class SQLPlannerLockRepository(PlannerLockRepository):
    """Row-lock based implementation of the planner lock."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def acquire(self) -> None:
        await self._check(shared=False)

    async def reject_if_plan_active(self) -> None:
        await self._check(shared=True)

    async def bind(self, plan_id: int) -> None:
        await self._session.execute(
            update(SQLPlannerLock)
            .where(SQLPlannerLock.id == LOCK_ROW_ID)
            .values(active_plan_id=plan_id)
        )

    async def release(self, plan_id: int) -> None:
        await self._session.execute(
            update(SQLPlannerLock)
            .where(
                SQLPlannerLock.id == LOCK_ROW_ID,
                SQLPlannerLock.active_plan_id == plan_id,
            )
            .values(active_plan_id=None)
        )

    async def _check(self, shared: bool) -> None:
        stmt = (
            select(SQLPlannerLock.active_plan_id)
            .where(SQLPlannerLock.id == LOCK_ROW_ID)
            .with_for_update(read=shared)
        )
        active_plan_id = (await self._session.execute(stmt)).scalar_one()
        if active_plan_id is not None:
            raise ExecutionInProgressException(
                f"Plan {active_plan_id} is currently active"
            )
