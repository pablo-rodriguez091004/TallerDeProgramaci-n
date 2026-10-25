from infrastructure.persistence.extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=False)
    second_last_name = db.Column(db.String(100), nullable=True)
    document_number = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    role = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active', server_default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.current_timestamp())

    # Relaciones. appointments tiene DOS FK hacia users (cliente y mecanico),
    # por eso cada relacion indica explicitamente su foreign_keys.
    business = db.relationship('Business', back_populates='owner', uselist=False)
    vehicles = db.relationship('Vehicle', back_populates='owner')
    client_appointments = db.relationship(
        'Appointment', foreign_keys='Appointment.client_user_id', back_populates='client'
    )
    mechanic_appointments = db.relationship(
        'Appointment', foreign_keys='Appointment.mechanic_user_id', back_populates='mechanic'
    )

    __table_args__ = (
        db.CheckConstraint("role IN ('client', 'mechanic', 'admin', 'owner')", name='check_user_role'),
        db.CheckConstraint("status IN ('active', 'inactive')", name='check_user_status'),
    )
