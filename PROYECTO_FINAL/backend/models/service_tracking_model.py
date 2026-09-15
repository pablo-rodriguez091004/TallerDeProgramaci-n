from db.conexion import db
from datetime import datetime

class ServiceTracking(db.Model):
    __tablename__ = 'service_tracking'

    tracking_id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.appointment_id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    current_mileage = db.Column(db.Integer, nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('received', 'diagnosing', 'in_repair', 'quality_check', 'ready_for_pickup', 'delivered')",
            name='check_tracking_status'
        ),
    )