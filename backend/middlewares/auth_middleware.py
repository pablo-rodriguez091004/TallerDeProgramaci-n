from functools import wraps
from flask import jsonify
from flask_login import current_user

from api.errors import ApiError, is_api_request


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

    En /api/v1 el error sale con el formato unico {"code","message","details"};
    en las rutas antiguas se mantiene {"error": "..."} que lee el frontend.
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                if is_api_request():
                    raise ApiError(401, 'unauthorized', 'Authentication required: log in via POST /auth/login')
                return jsonify({'error': 'Debes iniciar sesión para acceder a este recurso'}), 401

            if current_user.role not in allowed_roles:
                if is_api_request():
                    raise ApiError(403, 'forbidden', 'Your role is not allowed to perform this action',
                                   {'required_roles': list(allowed_roles), 'your_role': current_user.role})
                return jsonify({'error': 'No tienes permiso para realizar esta acción'}), 403

            return f(*args, **kwargs)
        return wrapped
    return decorator
