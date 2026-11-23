"""Schema definition"""

from uuid import UUID

from pydantic import BaseModel, Field
from src.application.dto import CaptureTaskDTO, PlanDTO, TaskAssignmentDTO
from src.domain.aggregates.plan import Plan, PlanStatus


class CaptureTaskSchema(BaseModel):
    """Task details"""

    request_id: str
    target_theta: float = Field(ge=0, lt=360)


class AssignedTaskSchema(BaseModel):
    """Tasks assigned to a satellite"""

    satellite_id: int
    satellite_name: str
    tasks: list[CaptureTaskSchema]


class CreatePlanRequest(BaseModel):
    """Request for executing a new plan"""

    assignments: list[AssignedTaskSchema] = Field(min_length=1)

    def to_dto(self) -> PlanDTO:
        return PlanDTO(
            assignments=[
                TaskAssignmentDTO(
                    satellite_id=assignment.satellite_id,
                    satellite_name=assignment.satellite_name,
                    tasks=[
                        CaptureTaskDTO(
                            request_id=task.request_id,
                            target_theta=task.target_theta,
                        )
                        for task in assignment.tasks
                    ],
                )
                for assignment in self.assignments
            ]
        )


class PlanAcceptedResponse(BaseModel):
    """Plan accepted for execution"""

    plan_id: UUID
    status: PlanStatus

    @classmethod
    def from_domain(cls, plan: Plan) -> "PlanAcceptedResponse":
        return cls(plan_id=plan.plan_uuid, status=plan.status)


class SatelliteSchema(BaseModel):
    """Satellite information"""

    satellite_id: int
    satellite_name: str
    initial_position: int
    angular_velocity: int
    capture_tolerance: int
    slew_distance: int


class ConstellationResponse(BaseModel):
    """Constellation details"""

    satellites: list[SatelliteSchema]
