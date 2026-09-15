from db.conexion import db

class Service(db.Model):
    __tablename__ = 'services'

    service_id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.business_id'), nullable=False)
    service_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    estimated_duration_minutes = db.Column(db.Integer, nullable=False)
    base_price = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')

    __table_args__ = (
        db.CheckConstraint("status IN ('active', 'inactive')", name='check_service_status'),
    )