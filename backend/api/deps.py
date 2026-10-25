"""Acceso de las rutas a los casos de uso cableados en bootstrap.py."""

from flask import current_app
from flask_login import current_user

from domain.shared.actor import Actor


def container():
    return current_app.extensions['mecatrack']


def actor():
    """El usuario de la sesion como Actor del dominio."""
    return Actor(user_id=current_user.user_id, role=current_user.role)
