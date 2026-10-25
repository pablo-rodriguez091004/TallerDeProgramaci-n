from flask import Blueprint, jsonify
from flask_login import current_user, login_required, login_user, logout_user

from api.auth import SessionUser
from api.deps import container
from api.legacy import json_body, missing_field

auth_bp = Blueprint('auth', __name__)

REGISTER_FIELDS = ['first_name', 'last_name', 'document_number', 'email', 'password']


@auth_bp.route('/register', methods=['POST'])
def register():
    data = json_body()
    error = missing_field(data, REGISTER_FIELDS)
    if error:
        return error
    user = container().auth.register(data, role='client')
    return jsonify({'message': 'Usuario registrado exitosamente', 'user_id': user.user_id}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = json_body()
    if 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Correo y contraseña son obligatorios'}), 400

    user = container().auth.authenticate(data['email'], data['password'])
    login_user(SessionUser(user))
    return jsonify({'message': 'Sesión iniciada', 'user_id': user.user_id, 'role': user.role}), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    return jsonify({
        'user_id': current_user.user_id,
        'first_name': current_user.first_name,
        'last_name': current_user.last_name,
        'email': current_user.email,
        'role': current_user.role
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Sesión cerrada'}), 200
