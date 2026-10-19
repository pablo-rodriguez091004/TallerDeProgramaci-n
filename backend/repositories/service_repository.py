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
