from db.conexion import db

class Bay(db.Model):
    __tablename__ = 'bays'

    bay_id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.business_id'), nullable=False)
    bay_number = db.Column(db.String(20), nullable=False)
    has_elevator = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(20), nullable=False, default='available')

    __table_args__ = (
        db.UniqueConstraint('business_id', 'bay_number', name='unique_business_bay_number'),
        db.CheckConstraint("status IN ('available', 'under_maintenance')", name='check_bay_status'),
    )