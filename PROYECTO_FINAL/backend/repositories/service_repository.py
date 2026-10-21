from db.conexion import db
from models.service_model import Service
from repositories import base_repository


def get_by_id(service_id):
    return db.session.get(Service, service_id)


def list_active():
    return Service.query.filter_by(status='active').order_by(Service.service_id).all()


def list_by_business(business_id):
    """Todos los servicios del negocio, incluidos los inactivos (vista admin)."""
    return Service.query.filter_by(business_id=business_id).order_by(Service.service_id).all()


def create(**fields):
    return base_repository.add(Service(**fields))


def list_by_status(status=None):
    """Catalogo de todos los negocios; status=None devuelve activos e inactivos."""
    query = Service.query
    if status:
        query = query.filter_by(status=status)
    return query.order_by(Service.service_id).all()


def find_by_name(business_id, service_name, exclude_id=None):
    """Busca un servicio del negocio con el mismo nombre, sin distinguir mayusculas."""
    query = Service.query.filter(
        Service.business_id == business_id,
        db.func.lower(Service.service_name) == service_name.lower(),
    )
    if exclude_id is not None:
        query = query.filter(Service.service_id != exclude_id)
    return query.first()


def count_appointments(service_id):
    from models.appointment_model import Appointment
    return Appointment.query.filter_by(service_id=service_id).count()


def delete(service):
    base_repository.delete(service)
