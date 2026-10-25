from abc import ABC, abstractmethod

from domain.tracking.entities import TrackingRecord


class TrackingRepository(ABC):
    @abstractmethod
    def list_by_appointment(self, appointment_id: int) -> list[TrackingRecord]:
        """Registros en orden cronologico, con los repuestos usados en cada uno."""

    @abstractmethod
    def add(self, record: TrackingRecord) -> TrackingRecord:
        """Guarda el registro y sus parts_used; devuelve la entidad con tracking_id."""
