from functools import wraps
from flask import jsonify
from flask_login import current_user


def role_required(*allowed_roles):
    """
    Decorador para proteger rutas segun el rol del usuario autenticado.

    Uso:
        @role_required('owner', 'admin')
        def crear_bahia():
            ...

    - Si no hay sesion activa -> 401 (no autenticado).
    - Si hay sesion pero el rol no esta permitido -> 403 (sin permiso).
    - Si el rol esta permitido -> ejecuta la funcion normalmente.
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Debes iniciar sesión para acceder a este recurso'}), 401

            if current_user.role not in allowed_roles:
                return jsonify({'error': 'No tienes permiso para realizar esta acción'}), 403

            return f(*args, **kwargs)
        return wrapped
    return decorator
