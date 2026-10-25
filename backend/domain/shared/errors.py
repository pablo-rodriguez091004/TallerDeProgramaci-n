"""
Errores de negocio. El dominio no sabe de HTTP: la capa api traduce cada
tipo a un codigo de estado (api/errors.py: DOMAIN_ERROR_STATUS).

`message` es el texto que ve el cliente; `code` y `details` solo los usa
/api/v1 (formato {"code","message","details"}).
"""


class DomainError(Exception):
    default_code = 'domain_error'

    def __init__(self, message, code=None, details=None):
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.details = details


class InvalidInput(DomainError):
    """Un dato no cumple una regla de negocio (estado, metodo de pago, ...)."""
    default_code = 'bad_request'


class NotFound(DomainError):
    default_code = 'not_found'


class PermissionDenied(DomainError):
    """El actor esta autenticado pero no puede operar sobre ese recurso."""
    default_code = 'forbidden'


class Conflict(DomainError):
    """El estado actual impide la operacion (duplicado, sin disponibilidad, ...)."""
    default_code = 'conflict'


class PersistenceConflict(Conflict):
    """El almacenamiento rechazo el cambio (p. ej. una restriccion UNIQUE)."""
    default_code = 'persistence_conflict'


class AuthenticationFailed(DomainError):
    """Credenciales invalidas."""
    default_code = 'unauthorized'
