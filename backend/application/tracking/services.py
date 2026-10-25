"""Casos de uso del seguimiento del servicio en el taller."""

from domain.catalog.ports import PartRepository
from domain.scheduling.ports import AppointmentRepository
from domain.scheduling.rules import ensure_participant
from domain.shared.errors import InvalidInput, NotFound, PermissionDenied
from domain.shared.ports import UnitOfWork
from domain.tracking.entities import TRACKING_STATUSES, PartUsage, TrackingRecord
from domain.tracking.ports import TrackingRepository


class TrackingService:

    def __init__(self, appointments: AppointmentRepository, tracking: TrackingRepository,
                 parts: PartRepository, uow: UnitOfWork):
        self._appointments = appointments
        self._tracking = tracking
        self._parts = parts
        self._uow = uow

    def list_for(self, actor, appointment_id):
        appointment = self._get_appointment(appointment_id)
        ensure_participant(actor, appointment, 'No tienes permiso para ver este seguimiento')
        return self._tracking.list_by_appointment(appointment_id)

    def record_step(self, actor, appointment_id, status, notes=None, current_mileage=None, parts_used=()):
        """
        El mecanico registra un paso del proceso con los repuestos usados, lo
        que descuenta stock. Todo se valida antes de escribir: si un repuesto
        falla no queda nada a medias.
        """
        appointment = self._get_appointment(appointment_id)
        if actor.is_mechanic and appointment.mechanic_user_id != actor.user_id:
            raise PermissionDenied('No tienes permiso para actualizar esta cita')
        if status not in TRACKING_STATUSES:
            raise InvalidInput(f'Estado inválido, debe ser uno de: {TRACKING_STATUSES}')

        usages, touched = [], {}
        for item in parts_used:
            part = touched.get(item.get('part_id')) or self._parts.get(item.get('part_id'))
            quantity = item.get('quantity', 1)
            if not part:
                raise InvalidInput(f"Repuesto {item.get('part_id')} no encontrado")
            if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
                raise InvalidInput('La cantidad de cada repuesto debe ser un entero mayor a 0')
            if part.stock_quantity < quantity:
                raise InvalidInput(f'No hay stock suficiente de {part.part_name}')
            part.stock_quantity -= quantity
            touched[part.part_id] = part
            usages.append(PartUsage(part_id=part.part_id, part_name=part.part_name, quantity=quantity))

        for part in touched.values():
            self._parts.save(part)
        record = self._tracking.add(TrackingRecord(appointment_id=appointment_id, status=status, notes=notes,
                                                   current_mileage=current_mileage, parts_used=usages))
        self._uow.commit()
        return record

    def _get_appointment(self, appointment_id):
        appointment = self._appointments.get(appointment_id)
        if not appointment:
            raise NotFound('Cita no encontrada')
        return appointment
