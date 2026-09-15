from db.conexion import db

class Part(db.Model):
    __tablename__ = 'parts'

    part_id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.business_id'), nullable=False)
    part_name = db.Column(db.String(100), nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default='active')

    __table_args__ = (
        db.CheckConstraint("status IN ('active', 'inactive')", name='check_part_status'),
    )