import asyncio
import logging
from collections.abc import Callable
from uuid import UUID

from src.application.ports.simulation_scheduler import SimulationScheduler
from src.application.use_cases.run_simulation import RunSimulationUseCase

logger = logging.getLogger(__name__)


class AsyncioSimulationScheduler(SimulationScheduler):
    """Runs simulations as background asyncio tasks in this process"""

    def __init__(
        self, run_simulation_factory: Callable[[], RunSimulationUseCase]
    ) -> None:
        self._run_simulation_factory = run_simulation_factory
        self._running: dict[UUID, asyncio.Task] = {}

    async def schedule(self, plan_uuid: UUID) -> None:
        use_case = self._run_simulation_factory()
        task = asyncio.create_task(
            use_case.execute(plan_uuid), name=f"simulation-{plan_uuid}"
        )
        self._running[plan_uuid] = task
        task.add_done_callback(lambda t: self._on_done(plan_uuid, t))

    def _on_done(self, plan_uuid: UUID, task: asyncio.Task) -> None:
        self._running.pop(plan_uuid, None)
        if not task.cancelled() and task.exception() is not None:
            logger.error("Simulation %s failed", plan_uuid)

    async def shutdown(self) -> None:
        for task in self._running.values():
            task.cancel()
        await asyncio.gather(*self._running.values(), return_exceptions=True)
