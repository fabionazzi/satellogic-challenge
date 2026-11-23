from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.aggregates.capture_task import CaptureTask
from src.domain.aggregates.plan import Plan
from src.domain.exceptions import (
    ExecutionInProgressError,
    NotPersistedError,
    PlanAlreadyExistsError,
)
from src.domain.repositories.capture_task_repository import (
    CaptureTaskRepository,
)
from src.domain.repositories.plan_repository import PlanRepository
from src.infrastructure.persistence.sql.mappers import (
    CaptureTaskMapper,
    PlanMapper,
)
from src.infrastructure.persistence.sql.models import (
    ACTIVE_SLOT_COLUMN,
    SQLCaptureTask,
    SQLPlan,
)


class SQLPlanRepository(PlanRepository):
    """SQLAlchemy implementation of the plan repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, plan: Plan) -> Plan:
        model = PlanMapper.to_new_model(plan)
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            if ACTIVE_SLOT_COLUMN in str(exc.orig):
                raise ExecutionInProgressError() from exc
            raise PlanAlreadyExistsError(plan.plan_uuid) from exc
        return PlanMapper.to_domain(model)

    async def get_by_uuid(self, plan_uuid: UUID) -> Plan | None:
        stmt = select(SQLPlan).where(SQLPlan.plan_uuid == plan_uuid)
        model = await self._session.scalar(stmt)
        return PlanMapper.to_domain(model) if model else None

    async def update(self, plan: Plan) -> None:
        if plan.plan_id is None:
            raise NotPersistedError("Plan must be added before being updated")
        model = await self._session.get(SQLPlan, plan.plan_id)
        if model is None:
            raise NotPersistedError(f"Plan {plan.plan_id} not found")
        PlanMapper.apply(plan, model)
        await self._session.flush()


class SQLCaptureTaskRepository(CaptureTaskRepository):
    """SQLAlchemy implementation of the capture task repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_many(
        self, capture_tasks: list[CaptureTask]
    ) -> list[CaptureTask]:
        models = [CaptureTaskMapper.to_new_model(t) for t in capture_tasks]
        self._session.add_all(models)
        await self._session.flush()
        return [CaptureTaskMapper.to_domain(m) for m in models]

    async def get(self, capture_task_id: int) -> CaptureTask | None:
        model = await self._session.get(SQLCaptureTask, capture_task_id)
        return CaptureTaskMapper.to_domain(model) if model else None

    async def update(self, capture_task: CaptureTask) -> CaptureTask:
        if capture_task.task_id is None:
            raise NotPersistedError("Task must be added before being updated")
        model = await self._session.get(SQLCaptureTask, capture_task.task_id)
        if model is None:
            raise NotPersistedError(f"Task {capture_task.task_id} not found")
        CaptureTaskMapper.apply(capture_task, model)
        await self._session.flush()
        return CaptureTaskMapper.to_domain(model)

    async def list_by_plan(self, plan_id: int) -> list[CaptureTask]:
        stmt = (
            select(SQLCaptureTask)
            .where(SQLCaptureTask.plan_id == plan_id)
            .order_by(SQLCaptureTask.task_id)
        )
        models = (await self._session.scalars(stmt)).all()
        return [CaptureTaskMapper.to_domain(m) for m in models]
