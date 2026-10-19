from db.conexion import db
from models.part_model import Part
from repositories import base_repository


def get_by_id(part_id):
    return db.session.get(Part, part_id)


def list_by_business(business_id, include_inactive=False):
    query = Part.query.filter_by(business_id=business_id)
    if not include_inactive:
        query = query.filter_by(status='active')
    return query.order_by(Part.part_id).all()


def create(**fields):
    return base_repository.add(Part(**fields))
