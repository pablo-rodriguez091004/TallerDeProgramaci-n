from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from db.conexion import db
from models.user_model import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    required_fields = ['first_name', 'last_name', 'document_number', 'email', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'El campo {field} es obligatorio'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Ese correo ya está registrado'}), 409

    if User.query.filter_by(document_number=data['document_number']).first():
        return jsonify({'error': 'Ese número de documento ya está registrado'}), 409

    nuevo_usuario = User(
        first_name=data['first_name'],
        middle_name=data.get('middle_name'),
        last_name=data['last_name'],
        second_last_name=data.get('second_last_name'),
        document_number=data['document_number'],
        email=data['email'],
        role='client',
        password_hash=generate_password_hash(data['password']),
        phone=data.get('phone')
    )

    db.session.add(nuevo_usuario)
    db.session.commit()

    return jsonify({'message': 'Usuario registrado exitosamente', 'user_id': nuevo_usuario.user_id}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Correo y contraseña son obligatorios'}), 400

    usuario = User.query.filter_by(email=data['email']).first()

    if not usuario or not check_password_hash(usuario.password_hash, data['password']):
        return jsonify({'error': 'Credenciales inválidas'}), 401

    login_user(usuario)

    return jsonify({'message': 'Sesión iniciada', 'user_id': usuario.user_id, 'role': usuario.role}), 200


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Sesión cerrada'}), 200