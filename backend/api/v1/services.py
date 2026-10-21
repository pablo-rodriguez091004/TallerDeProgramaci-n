"""
CRUD del catalogo de servicios en /api/v1/services.

- Lectura (GET) publica: el catalogo se muestra antes de iniciar sesion.
- Escritura (POST/PUT/DELETE) solo para 'owner' y 'admin', con el mismo
  middleware de roles que usan las rutas antiguas.
- A diferencia de DELETE /services (borrado logico), aqui DELETE elimina el
  registro y responde 409 si el servicio ya tiene citas: borrarlo dejaria
  citas huerfanas. Para retirarlo del catalogo se usa PUT con status='inactive'.
"""

from flask.views import MethodView
from flask_login import current_user
from flask_smorest import Blueprint
from sqlalchemy.exc import IntegrityError

from api.errors import ApiError
from middlewares.auth_middleware import role_required
from repositories import base_repository, business_repository, service_repository
from schemas.service_schema import ServiceInputSchema, ServiceQuerySchema, ServiceSchema

blp = Blueprint('services_v1', __name__, description='Workshop service catalog (CRUD).')

WRITE_ROLES = ('owner', 'admin')
# role_required va por fuera de los decoradores de smorest: primero se valida
# la sesion (401/403) y despues el cuerpo (422). functools.wraps conserva la
# documentacion OpenAPI que smorest guarda en la funcion.


def _get_or_404(service_id):
    service = service_repository.get_by_id(service_id)
    if not service:
        raise ApiError(404, 'not_found', f'Service {service_id} was not found', {'service_id': service_id})
    return service


def _ensure_unique_name(business_id, service_name, exclude_id=None):
    duplicate = service_repository.find_by_name(business_id, service_name, exclude_id)
    if duplicate:
        raise ApiError(409, 'duplicate_service_name',
                       f"A service named '{service_name}' already exists",
                       {'service_name': service_name, 'existing_service_id': duplicate.service_id})


def _commit_or_conflict(service_name):
    # La restriccion UNIQUE(business_id, service_name) cubre la carrera entre
    # dos peticiones simultaneas que pasan el chequeo previo.
    try:
        base_repository.commit()
    except IntegrityError:
        base_repository.rollback()
        raise ApiError(409, 'duplicate_service_name',
                       f"A service named '{service_name}' already exists", {'service_name': service_name})


@blp.route('')
class ServiceCollection(MethodView):

    @blp.arguments(ServiceQuerySchema, location='query')
    @blp.response(200, ServiceSchema(many=True))
    def get(self, query):
        """List services

        Returns the service catalog ordered by id. By default only active
        services are returned; use `status=all` to include inactive ones.
        Public endpoint, no authentication required.
        """
        status = None if query['status'] == 'all' else query['status']
        return service_repository.list_by_status(status)

    @role_required(*WRITE_ROLES)
    @blp.arguments(ServiceInputSchema)
    @blp.response(201, ServiceSchema)
    def post(self, data):
        """Create a service

        Adds a new service to the catalog of the authenticated user's
        workshop. Requires an `owner` or `admin` session.
        """
        business = business_repository.get_for_user(current_user)
        if not business:
            raise ApiError(403, 'business_not_linked', 'Your account is not linked to a workshop')

        _ensure_unique_name(business.business_id, data['service_name'])
        service = service_repository.create(business_id=business.business_id, **data)
        _commit_or_conflict(data['service_name'])
        return service


@blp.route('/<int:service_id>')
class ServiceItem(MethodView):

    @blp.response(200, ServiceSchema)
    def get(self, service_id):
        """Get a service

        Returns a single service by its id, active or inactive.
        Public endpoint, no authentication required.
        """
        return _get_or_404(service_id)

    @role_required(*WRITE_ROLES)
    @blp.arguments(ServiceInputSchema)
    @blp.response(200, ServiceSchema)
    def put(self, data, service_id):
        """Replace a service

        Replaces every editable field of the service (full representation,
        not a partial update). Requires an `owner` or `admin` session.
        """
        service = _get_or_404(service_id)
        _ensure_unique_name(service.business_id, data['service_name'], exclude_id=service_id)
        for field, value in data.items():
            setattr(service, field, value)
        _commit_or_conflict(data['service_name'])
        return service

    @role_required(*WRITE_ROLES)
    @blp.response(204)
    def delete(self, service_id):
        """Delete a service

        Permanently deletes a service that has never been booked. If any
        appointment references it, the API answers 409; deactivate it with
        PUT (`status: inactive`) instead. Requires an `owner` or `admin` session.
        """
        service = _get_or_404(service_id)
        appointments = service_repository.count_appointments(service_id)
        if appointments:
            raise ApiError(409, 'service_has_appointments',
                           f'Service {service_id} has {appointments} appointment(s) and cannot be deleted',
                           {'service_id': service_id, 'appointments': appointments})
        service_repository.delete(service)
        base_repository.commit()
