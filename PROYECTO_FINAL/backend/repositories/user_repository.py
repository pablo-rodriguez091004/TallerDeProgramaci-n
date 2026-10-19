from db.conexion import db
from models.user_model import User
from repositories import base_repository


def get_by_id(user_id):
    return db.session.get(User, user_id)


def get_by_email(email):
    return User.query.filter_by(email=email).first()


def get_by_document(document_number):
    return User.query.filter_by(document_number=document_number).first()


def list_mechanics(only_active=False):
    query = User.query.filter_by(role='mechanic')
    if only_active:
        query = query.filter_by(status='active')
    return query.order_by(User.user_id).all()


def create(**fields):
    return base_repository.add(User(**fields))
