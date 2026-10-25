"""
API REST versionada (/api/v1) documentada con OpenAPI 3 via flask-smorest.

Solo los blueprints registrados con `api.register_blueprint` aparecen en la
especificacion; las rutas antiguas del frontend quedan intactas.

- Especificacion JSON: GET /openapi.json
- Swagger UI:          GET /docs
"""

from flask_smorest import Api as SmorestApi

from api.errors import error_response, is_api_request
from api.v1.schemas.error_schema import ApiErrorSchema

API_DESCRIPTION = """
REST API of **MecaTrack**, a booking and vehicle-tracking system for a car repair workshop.

* **Errors** always use the same JSON body: `{"code": "...", "message": "...", "details": ...}`.
* **Authentication** is a session cookie. In Swagger UI, call `POST /auth/login` first
  (for example with `carlos.owner@tallermecanico.com` / `test1234`, the test owner listed in the README);
  the browser keeps the cookie and sends it on the following requests.
* **Roles**: reading the catalog is public; creating, replacing or deleting services
  requires the `owner` or `admin` role, and so does the open-data market panel (`/api/v1/market`).
""".strip()

# /auth/login y /auth/logout son rutas antiguas (no smorest). Se documentan a
# mano para que Swagger UI pueda iniciar sesion y probar POST/PUT/DELETE.
LEGACY_ERROR = {'type': 'object', 'properties': {'error': {
    'type': 'string', 'description': 'Error message in Spanish (legacy format of the /auth routes).',
    'example': 'Credenciales inválidas'}}}

AUTH_PATHS = {
    '/auth/login': {'post': {
        'tags': ['Auth'],
        'summary': 'Log in',
        'description': 'Starts a session and sets the `session` cookie used by the protected endpoints. '
                       'This is a pre-existing route, so its errors use the legacy `{"error": "..."}` body.',
        'requestBody': {'required': True, 'content': {'application/json': {
            'schema': {'type': 'object', 'required': ['email', 'password'], 'properties': {
                'email': {'type': 'string', 'format': 'email', 'description': 'Account email.',
                          'example': 'carlos.owner@tallermecanico.com'},
                'password': {'type': 'string', 'format': 'password', 'description': 'Account password.',
                             'example': 'test1234'}}},
            'example': {'email': 'carlos.owner@tallermecanico.com', 'password': 'test1234'}}}},
        'responses': {
            '200': {'description': 'Session started; the response sets the `session` cookie.',
                    'content': {'application/json': {
                        'schema': {'type': 'object', 'properties': {
                            'message': {'type': 'string', 'description': 'Confirmation message.',
                                        'example': 'Sesión iniciada'},
                            'user_id': {'type': 'integer', 'description': 'Id of the logged-in user.', 'example': 1},
                            'role': {'type': 'string', 'description': 'Role of the user.', 'example': 'owner'}}},
                        'example': {'message': 'Sesión iniciada', 'user_id': 1, 'role': 'owner'}}}},
            '400': {'description': 'Email or password missing.', 'content': {'application/json': {
                'schema': LEGACY_ERROR, 'example': {'error': 'Correo y contraseña son obligatorios'}}}},
            '401': {'description': 'Wrong credentials.', 'content': {'application/json': {
                'schema': LEGACY_ERROR, 'example': {'error': 'Credenciales inválidas'}}}},
            '403': {'description': 'The account is inactive.', 'content': {'application/json': {
                'schema': LEGACY_ERROR, 'example': {'error': 'Tu cuenta está inactiva'}}}},
        }}},
    '/auth/logout': {'post': {
        'tags': ['Auth'],
        'summary': 'Log out',
        'description': 'Ends the current session. Pre-existing route (legacy error format).',
        'security': [{'cookieAuth': []}],
        'responses': {
            '200': {'description': 'Session closed.', 'content': {'application/json': {
                'schema': {'type': 'object', 'properties': {'message': {
                    'type': 'string', 'description': 'Confirmation message.', 'example': 'Sesión cerrada'}}},
                'example': {'message': 'Sesión cerrada'}}}},
            '401': {'description': 'There was no active session.', 'content': {'application/json': {
                'schema': LEGACY_ERROR,
                'example': {'error': 'Debes iniciar sesión para acceder a este recurso'}}}},
        }}},
}


class Api(SmorestApi):
    # Las respuestas de error que smorest agrega solo (p. ej. el 422 de
    # @blp.arguments) usan el formato unico de la API.
    ERROR_SCHEMA = ApiErrorSchema
    # Sin respuesta "default" generica: cada endpoint declara sus errores.
    DEFAULT_ERROR_RESPONSE_NAME = None

    def handle_http_exception(self, error):
        # flask-smorest registra este manejador para TODA la app. Fuera de
        # /api/ se devuelve el error tal cual (comportamiento por defecto de
        # Flask), para no cambiar las respuestas de las rutas antiguas.
        if not is_api_request():
            return error
        return error_response(error)


api = Api()


def init_api(app):
    app.config.setdefault('API_SPEC_OPTIONS', {
        'info': {'description': API_DESCRIPTION,
                 'contact': {'name': 'MecaTrack team - Universidad Manuela Beltran'}},
        'servers': [{'url': 'http://127.0.0.1:5000', 'description': 'Local development server'}],
        'tags': [{'name': 'Auth', 'description': 'Session management (pre-existing routes).'}],
        'components': {'securitySchemes': {'cookieAuth': {
            'type': 'apiKey', 'in': 'cookie', 'name': 'session',
            'description': 'Flask session cookie returned by POST /auth/login.'}}},
    })
    api.init_app(app)
    # smorest registra siempre el esquema de paginacion; esta API no pagina,
    # asi que se quita para que el spec solo muestre lo que realmente se usa.
    api.spec.components.headers_lazy.pop('PAGINATION', None)
    api.spec.components.schemas.pop('PaginationMetadata', None)

    rules = {rule.rule: rule for rule in app.url_map.iter_rules()}
    for path, operations in AUTH_PATHS.items():
        api.spec.path(rule=rules[path], operations=operations)

    from api.v1.ai import blp as ai_blp
    from api.v1.market import blp as market_blp
    from api.v1.services import blp as services_blp

    api.register_blueprint(services_blp, url_prefix='/api/v1/services')
    api.register_blueprint(ai_blp, url_prefix='/api/v1/ai')
    api.register_blueprint(market_blp, url_prefix='/api/v1/market')
