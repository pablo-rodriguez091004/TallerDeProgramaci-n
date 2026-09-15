from flask import Flask
from config import Config
from db.conexion import db, login_manager
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5500"])

    db.init_app(app)
    login_manager.init_app(app)

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

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
