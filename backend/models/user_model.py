from db.conexion import db, login_manager
from datetime import datetime
from flask_login import UserMixin

class User(db.Model, UserMixin):
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
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint("role IN ('client', 'mechanic', 'admin', 'owner')", name='check_user_role'),
        db.CheckConstraint("status IN ('active', 'inactive')", name='check_user_status'),
    )

    def get_id(self):
        return str(self.user_id)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))