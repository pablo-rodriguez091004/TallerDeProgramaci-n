from models.service_tracking_model import ServiceTracking
from models.service_tracking_parts_model import ServiceTrackingPart
from repositories import base_repository


def list_by_appointment(appointment_id):
    return (ServiceTracking.query.filter_by(appointment_id=appointment_id)
            .order_by(ServiceTracking.recorded_at).all())


def create(**fields):
    return base_repository.add(ServiceTracking(**fields))


def add_part_usage(tracking_id, part_id, quantity):
    return base_repository.add(ServiceTrackingPart(tracking_id=tracking_id, part_id=part_id, quantity=quantity))
