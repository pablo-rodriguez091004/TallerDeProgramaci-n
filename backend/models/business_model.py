from db.conexion import db

class Business(db.Model):
    __tablename__ = 'businesses'

    business_id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(150), nullable=False)
    tax_id = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    business_phone = db.Column(db.String(20), nullable=True)
    business_registration_number = db.Column(db.String(50), nullable=True)
    legal_documents_verified = db.Column(db.Boolean, default=False)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, unique=True)