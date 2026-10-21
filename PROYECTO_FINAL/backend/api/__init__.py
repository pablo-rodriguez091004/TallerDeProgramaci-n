"""
API REST versionada (/api/v1) documentada con OpenAPI 3 via flask-smorest.

Solo los blueprints registrados con `api.register_blueprint` aparecen en la
especificacion; las rutas antiguas del frontend quedan intactas.
"""

from flask_smorest import Api as SmorestApi

from api.errors import error_response, is_api_request


class Api(SmorestApi):
    def handle_http_exception(self, error):
        # flask-smorest registra este manejador para TODA la app. Fuera de
        # /api/ se devuelve el error tal cual (comportamiento por defecto de
        # Flask), para no cambiar las respuestas de las rutas antiguas.
        if not is_api_request():
            return error
        return error_response(error)


api = Api()


def init_api(app):
    api.init_app(app)

    from api.v1.services import blp as services_blp

    api.register_blueprint(services_blp, url_prefix='/api/v1/services')
