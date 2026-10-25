from domain.catalog.entities import Service
from domain.catalog.ports import ServiceRepository
from infrastructure.persistence.extensions import db
from infrastructure.persistence.models.appointment_model import Appointment as AppointmentRow
from infrastructure.persistence.models.service_model import Service as ServiceRow
from infrastructure.persistence.repositories.base_repository import SqlAlchemyRepository


class SqlAlchemyServiceRepository(SqlAlchemyRepository, ServiceRepository):
    model, entity, pk = ServiceRow, Service, 'service_id'

    def list_active(self):
        return self.list_by_status('active')

    def list_by_business(self, business_id):
        """Todos los servicios del taller, incluidos los inactivos (vista admin)."""
        return self._to_entities(ServiceRow.query.filter_by(business_id=business_id).order_by(ServiceRow.service_id))

    def list_by_status(self, status=None):
        """Catalogo de todos los talleres; status=None devuelve activos e inactivos."""
        query = ServiceRow.query
        if status:
            query = query.filter_by(status=status)
        return self._to_entities(query.order_by(ServiceRow.service_id))

    def find_by_name(self, business_id, service_name, exclude_id=None):
        query = ServiceRow.query.filter(
            ServiceRow.business_id == business_id,
            db.func.lower(ServiceRow.service_name) == service_name.lower(),
        )
        if exclude_id is not None:
            query = query.filter(ServiceRow.service_id != exclude_id)
        return self.to_entity(query.first())

    def count_appointments(self, service_id):
        return AppointmentRow.query.filter_by(service_id=service_id).count()
