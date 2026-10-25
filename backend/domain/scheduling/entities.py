from dataclasses import dataclass
from datetime import datetime
from typing import Optional

APPOINTMENT_STATUSES = ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled')
# Estados que "ocupan" una bahia o un mecanico en el tiempo. Una cita
# cancelada o completada ya no bloquea ese horario.
BLOCKING_STATUSES = ('pending', 'confirmed', 'in_progress')
FINAL_STATUSES = ('completed', 'cancelled')


@dataclass(kw_only=True)
class Appointment:
    appointment_id: Optional[int] = None
    client_user_id: int
    vehicle_id: int
    service_id: int
    bay_id: int
    mechanic_user_id: int
    scheduled_start: datetime
    scheduled_end: datetime
    status: str = 'pending'
    created_at: Optional[datetime] = None

    @property
    def can_be_cancelled(self):
        return self.status not in FINAL_STATUSES


@dataclass(kw_only=True)
class AppointmentView:
    """Modelo de lectura: la cita con los nombres de sus relaciones."""
    appointment: Appointment
    client_name: Optional[str]
    mechanic_name: Optional[str]
    vehicle_plate: Optional[str]
    service_name: Optional[str]
    bay_number: Optional[str]
