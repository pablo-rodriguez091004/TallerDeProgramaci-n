from db.conexion import db
from datetime import datetime

class Appointment(db.Model):
    __tablename__ = 'appointments'

    appointment_id = db.Column(db.Integer, primary_key=True)
    client_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.vehicle_id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.service_id'), nullable=False)
    bay_id = db.Column(db.Integer, db.ForeignKey('bays.bay_id'), nullable=False)
    mechanic_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    scheduled_start = db.Column(db.DateTime, nullable=False)
    scheduled_end = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled')",
            name='check_appointment_status'
        ),
    )