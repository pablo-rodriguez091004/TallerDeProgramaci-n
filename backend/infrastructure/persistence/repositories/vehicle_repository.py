from domain.catalog.entities import Vehicle
from domain.catalog.ports import VehicleRepository
from infrastructure.persistence.extensions import db
from infrastructure.persistence.models.appointment_model import Appointment as AppointmentRow
from infrastructure.persistence.models.vehicle_model import Vehicle as VehicleRow
from infrastructure.persistence.repositories.base_repository import SqlAlchemyRepository


class SqlAlchemyVehicleRepository(SqlAlchemyRepository, VehicleRepository):
    model, entity, pk = VehicleRow, Vehicle, 'vehicle_id'

    def get_by_plate(self, license_plate):
        return self.to_entity(VehicleRow.query.filter_by(license_plate=license_plate).first())

    def list_by_owner(self, owner_user_id):
        return self._to_entities(VehicleRow.query.filter_by(owner_user_id=owner_user_id).order_by(VehicleRow.vehicle_id))

    def has_appointments(self, vehicle_id):
        return db.session.query(AppointmentRow.query.filter_by(vehicle_id=vehicle_id).exists()).scalar()
