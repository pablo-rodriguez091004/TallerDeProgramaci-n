from db.conexion import db
from models.bay_model import Bay
from repositories import base_repository


def get_by_id(bay_id):
    return db.session.get(Bay, bay_id)


def get_by_number(business_id, bay_number):
    return Bay.query.filter_by(business_id=business_id, bay_number=bay_number).first()


def list_by_business(business_id, only_available=False):
    query = Bay.query.filter_by(business_id=business_id)
    if only_available:
        query = query.filter_by(status='available')
    return query.order_by(Bay.bay_id).all()


def create(**fields):
    return base_repository.add(Bay(**fields))
