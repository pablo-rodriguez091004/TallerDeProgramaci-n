"""
Operaciones comunes de la sesion de SQLAlchemy.

Los repositorios agregan objetos a la sesion (add + flush) pero NO hacen
commit: la ruta decide cuando termina la unidad de trabajo. Asi, por
ejemplo, crear una cita y sus dos pagos queda en una sola transaccion.
"""

from db.conexion import db


def add(obj):
    db.session.add(obj)
    db.session.flush()  # asigna el id sin cerrar la transaccion
    return obj


def delete(obj):
    db.session.delete(obj)


def commit():
    db.session.commit()


def rollback():
    db.session.rollback()
