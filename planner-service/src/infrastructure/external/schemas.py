from pydantic import BaseModel
from src.domain.value_objects.satellite import Satellite, SatelliteAssignment


class SatelliteDTO(BaseModel):
    satellite_id: int
    satellite_name: str
    initial_position: int
    angular_velocity: int
    capture_tolerance: int
    slew_distance: int

    def to_domain(self) -> Satellite:
        return Satellite(**self.model_dump())


class ConstellationResponseDTO(BaseModel):
    satellites: list[SatelliteDTO]


class TaskAssignmentDTO(BaseModel):
    request_id: str
    target_theta: float


class SatelliteAssignmentDTO(BaseModel):
    satellite_id: int
    satellite_name: str
    tasks: list[TaskAssignmentDTO]


class ExecutionPlanRequestDTO(BaseModel):
    assignments: list[SatelliteAssignmentDTO]

    @classmethod
    def from_domain(
        cls, plan: list[SatelliteAssignment]
    ) -> "ExecutionPlanRequestDTO":
        return cls(
            assignments=[
                SatelliteAssignmentDTO(
                    satellite_id=assignment.satellite_id,
                    satellite_name=assignment.satellite_name,
                    tasks=[
                        TaskAssignmentDTO(
                            request_id=task.request_id,
                            target_theta=task.target_theta,
                        )
                        for task in assignment.tasks
                    ],
                )
                for assignment in plan
            ]
        )
