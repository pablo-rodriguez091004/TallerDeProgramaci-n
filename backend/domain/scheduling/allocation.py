"""
Motor de agendamiento: encuentra una bahia y un mecanico disponibles para
una franja horaria, sin solapamientos.

Regla de negocio (definida por Pablo en el diseño de la base de datos): la
disponibilidad se resuelve en el backend, no con constraints avanzados de
PostgreSQL (EXCLUDE), porque es la logica central del sistema.

Es un servicio de DOMINIO: no sabe de SQL. Recibe por constructor los
puertos que necesita y la consulta de solapamiento la resuelve el adaptador
(en SQL, sin traer todas las citas a memoria).

Simplificacion conocida: users no tiene business_id, asi que cualquier
mecanico activo puede ser asignado (hoy solo existe un taller).
"""

from domain.catalog.ports import BayRepository
from domain.identity.ports import UserRepository
from domain.scheduling.ports import AppointmentRepository


class ResourceAllocator:

    def __init__(self, bays: BayRepository, users: UserRepository, appointments: AppointmentRepository):
        self._bays = bays
        self._users = users
        self._appointments = appointments

    def find_available_bay(self, business_id, scheduled_start, scheduled_end, exclude_appointment_id=None):
        """Primera bahia 'available' del taller sin cita bloqueante solapada, o None."""
        for bay in self._bays.list_by_business(business_id, only_available=True):
            if not self._appointments.has_blocking_overlap(
                    scheduled_start, scheduled_end, bay_id=bay.bay_id,
                    exclude_appointment_id=exclude_appointment_id):
                return bay
        return None

    def find_available_mechanic(self, scheduled_start, scheduled_end, exclude_appointment_id=None):
        """Primer mecanico activo sin cita bloqueante solapada, o None."""
        for mechanic in self._users.list_mechanics(only_active=True):
            if not self._appointments.has_blocking_overlap(
                    scheduled_start, scheduled_end, mechanic_user_id=mechanic.user_id,
                    exclude_appointment_id=exclude_appointment_id):
                return mechanic
        return None

    def find_bay_and_mechanic(self, business_id, scheduled_start, scheduled_end, exclude_appointment_id=None):
        """
        Solo tiene sentido crear la cita si HAY bahia Y mecanico disponibles
        simultaneamente. Devuelve (bay, mechanic) o (None, None).
        """
        bay = self.find_available_bay(business_id, scheduled_start, scheduled_end, exclude_appointment_id)
        if not bay:
            return None, None
        mechanic = self.find_available_mechanic(scheduled_start, scheduled_end, exclude_appointment_id)
        if not mechanic:
            return None, None
        return bay, mechanic
