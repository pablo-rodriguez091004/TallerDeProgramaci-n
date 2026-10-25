"""
Formato unico de error para la API publica /api/v1:

    {"code": "not_found", "message": "Service 42 was not found", "details": null}

- `code`: identificador estable en snake_case (lo usa el cliente para decidir).
- `message`: texto legible en ingles.
- `details`: informacion extra (por ejemplo, errores de validacion por campo).

Las rutas antiguas (/services, /auth, ...) NO usan este formato: el frontend
lee la clave 'error' y no se debe romper.
"""

from flask import jsonify, request
from werkzeug.exceptions import HTTPException

from domain.shared.errors import (AuthenticationFailed, Conflict, DomainError, InvalidInput, NotFound,
                                  PermissionDenied)

API_PREFIX = '/api/'

# Codigo por defecto segun el estado HTTP cuando el error no trae uno propio
# (por ejemplo, 404 de una ruta inexistente o 405 de un metodo no permitido).
DEFAULT_CODES = {
    400: 'bad_request',
    401: 'unauthorized',
    403: 'forbidden',
    404: 'not_found',
    405: 'method_not_allowed',
    409: 'conflict',
    415: 'unsupported_media_type',
    422: 'validation_error',
    429: 'rate_limited',
    500: 'internal_error',
    502: 'bad_gateway',
    503: 'service_unavailable',
    504: 'gateway_timeout',
}


class ApiError(HTTPException):
    """Error de negocio de la API con codigo y detalles propios."""

    def __init__(self, status, code, message, details=None, headers=None):
        super().__init__(description=message)
        self.code = status
        self.error_code = code
        self.message = message
        self.details = details
        self.extra_headers = headers or {}


def is_api_request():
    return request.path.startswith(API_PREFIX)


def error_response(error):
    """Convierte cualquier HTTPException en la respuesta JSON del formato unico."""
    status = error.code or 500
    headers = {}

    if isinstance(error, ApiError):
        code, message, details = error.error_code, error.message, error.details
        headers = error.extra_headers
    else:
        code = DEFAULT_CODES.get(status, 'error')
        data = getattr(error, 'data', None) or {}
        message = data.get('message') or error.description
        details = data.get('errors') or data.get('messages')
        headers = data.get('headers') or {}
        if status == 422 and details:
            # webargs agrupa los errores por ubicacion: {"json": {...}}.
            # Si solo hay una ubicacion se aplana para que el cliente vea
            # directamente {"campo": ["mensaje"]}.
            if len(details) == 1:
                details = next(iter(details.values()))
            message = 'The request body is invalid'
        if status == 500:
            # Nunca se expone el detalle interno de un error inesperado.
            message, details = 'An unexpected error occurred', None

    response = jsonify({'code': code, 'message': message, 'details': details})
    response.status_code = status
    for name, value in headers.items():
        response.headers[name] = value
    return response


# El dominio no conoce HTTP: aqui se decide el estado de cada tipo de error.
DOMAIN_ERROR_STATUS = (
    (AuthenticationFailed, 401),
    (PermissionDenied, 403),
    (NotFound, 404),
    (Conflict, 409),
    (InvalidInput, 400),
)


def domain_error_status(error):
    for error_type, status in DOMAIN_ERROR_STATUS:
        if isinstance(error, error_type):
            return status
    return 400


def handle_domain_error(error: DomainError):
    """
    Un solo manejador para toda la app:
    - /api/v1 -> formato unico {"code","message","details"}
    - rutas antiguas -> {"error": "..."} (lo lee el frontend)
    """
    status = domain_error_status(error)
    if is_api_request():
        return error_response(ApiError(status, error.code, error.message, error.details))
    return jsonify({'error': error.message}), status
