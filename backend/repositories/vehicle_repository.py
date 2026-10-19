from db.conexion import db
from models.vehicle_model import Vehicle
from models.appointment_model import Appointment
from repositories import base_repository


def get_by_id(vehicle_id):
    return db.session.get(Vehicle, vehicle_id)


def get_by_plate(license_plate):
    return Vehicle.query.filter_by(license_plate=license_plate).first()


def list_by_owner(owner_user_id):
    return Vehicle.query.filter_by(owner_user_id=owner_user_id).order_by(Vehicle.vehicle_id).all()


def has_appointments(vehicle_id):
    return db.session.query(Appointment.query.filter_by(vehicle_id=vehicle_id).exists()).scalar()


def create(**fields):
    return base_repository.add(Vehicle(**fields))


def delete(vehicle):
    base_repository.delete(vehicle)
