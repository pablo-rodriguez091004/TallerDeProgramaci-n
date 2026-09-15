from db.conexion import db

class ServiceTrackingPart(db.Model):
    __tablename__ = 'service_tracking_parts'

    tracking_id = db.Column(db.Integer, db.ForeignKey('service_tracking.tracking_id'), primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.part_id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)