from db.conexion import db
from models.payment_model import Payment
from repositories import base_repository


def get_by_id(payment_id):
    return db.session.get(Payment, payment_id)


def list_by_appointment(appointment_id):
    return Payment.query.filter_by(appointment_id=appointment_id).order_by(Payment.payment_id).all()


def create(**fields):
    return base_repository.add(Payment(**fields))
