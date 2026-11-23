from abc import ABC, abstractmethod

from src.domain.value_objects.satellite_spec import SatelliteSpec


class ConstellationRepository(ABC):
    """Interface for constellation repositories"""

    @abstractmethod
    def get_all(self) -> list[SatelliteSpec]: ...
