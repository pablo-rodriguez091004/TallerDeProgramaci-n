from flask import Flask, jsonify
from config import Config
from db.conexion import db, login_manager, migrate
from flask_cors import CORS
from api.errors import ApiError, error_response, is_api_request

def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    CORS(app, supports_credentials=True, origins=app.config['CORS_ORIGINS'])

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from models.user_model import User
    from models.business_model import Business
    from models.vehicle_model import Vehicle
    from models.bay_model import Bay
    from models.service_model import Service
    from models.appointment_model import Appointment
    from models.payment_model import Payment
    from models.part_model import Part
    from models.service_tracking_model import ServiceTracking
    from models.service_tracking_parts_model import ServiceTrackingPart

    from routes.auth_routes import auth_bp
    from routes.vehicle_routes import vehicle_bp
    from routes.service_routes import service_bp
    from routes.business_routes import business_bp
    from routes.bay_routes import bay_bp
    from routes.part_routes import part_bp
    from routes.appointment_routes import appointment_bp
    from routes.payment_routes import payment_bp
    from routes.service_tracking_routes import tracking_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(vehicle_bp, url_prefix='/vehicles')
    app.register_blueprint(service_bp, url_prefix='/services')
    app.register_blueprint(business_bp, url_prefix='/businesses')
    app.register_blueprint(bay_bp, url_prefix='/bays')
    app.register_blueprint(part_bp, url_prefix='/parts')
    app.register_blueprint(appointment_bp, url_prefix='/appointments')
    app.register_blueprint(payment_bp, url_prefix='/payments')
    app.register_blueprint(tracking_bp, url_prefix='/tracking')

    # API REST v1 documentada con OpenAPI (flask-smorest). Va despues de los
    # blueprints antiguos y no los modifica.
    from api import init_api
    init_api(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        if is_api_request():
            return error_response(ApiError(401, 'unauthorized', 'Authentication required: log in via POST /auth/login'))
        return jsonify({'error': 'Debes iniciar sesión para acceder a este recurso'}), 401

    return app


# 'flask --app app db ...' (Flask-Migrate) encuentra create_app() solo.
if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)
