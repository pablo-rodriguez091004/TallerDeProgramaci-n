from flask import Blueprint, request, jsonify
from flask_login import current_user
from werkzeug.security import generate_password_hash
from middlewares.auth_middleware import role_required
from repositories import base_repository, business_repository, user_repository

business_bp = Blueprint('businesses', __name__)


@business_bp.route('/mine', methods=['GET'])
@role_required('owner')
def get_my_business():
    business = business_repository.get_by_owner(current_user.user_id)
    if not business:
        return jsonify({'error': 'No tienes un negocio registrado'}), 404
    return jsonify(_serialize_business(business)), 200


@business_bp.route('/mine', methods=['PUT'])
@role_required('owner')
def update_my_business():
    business = business_repository.get_by_owner(current_user.user_id)
    if not business:
        return jsonify({'error': 'No tienes un negocio registrado'}), 404

    data = request.get_json(silent=True) or {}
    editable_fields = ['business_name', 'address', 'business_phone', 'business_registration_number']
    for field in editable_fields:
        if field in data:
            setattr(business, field, data[field])

    base_repository.commit()
    return jsonify({'message': 'Negocio actualizado'}), 200


@business_bp.route('/mechanics', methods=['POST'])
@role_required('owner')
def create_mechanic():
    """
    El dueño crea la cuenta de un mecanico directamente (a diferencia del
    registro publico en /auth/register, que solo permite rol 'client').
    """
    data = request.get_json(silent=True) or {}
    required_fields = ['first_name', 'last_name', 'document_number', 'email', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'El campo {field} es obligatorio'}), 400

    if user_repository.get_by_email(data['email']):
        return jsonify({'error': 'Ese correo ya está registrado'}), 409
    if user_repository.get_by_document(data['document_number']):
        return jsonify({'error': 'Ese número de documento ya está registrado'}), 409

    mechanic = user_repository.create(
        first_name=data['first_name'],
        middle_name=data.get('middle_name'),
        last_name=data['last_name'],
        second_last_name=data.get('second_last_name'),
        document_number=data['document_number'],
        email=data['email'],
        role='mechanic',
        password_hash=generate_password_hash(data['password']),
        phone=data.get('phone')
    )
    base_repository.commit()

    return jsonify({'message': 'Mecánico creado', 'user_id': mechanic.user_id}), 201


@business_bp.route('/mechanics', methods=['GET'])
@role_required('owner', 'admin')
def list_mechanics():
    mechanics = user_repository.list_mechanics()
    return jsonify([_serialize_mechanic(m) for m in mechanics]), 200


@business_bp.route('/mechanics/<int:user_id>', methods=['PUT'])
@role_required('owner')
def update_mechanic(user_id):
    """
    Activa o desactiva a un mecanico. Un mecanico inactivo no puede iniciar
    sesion y el motor de agendamiento deja de asignarle citas nuevas.
    """
    mechanic = user_repository.get_by_id(user_id)
    if not mechanic or mechanic.role != 'mechanic':
        return jsonify({'error': 'Mecánico no encontrado'}), 404

    data = request.get_json(silent=True) or {}
    if 'status' in data:
        if data['status'] not in ('active', 'inactive'):
            return jsonify({'error': "Estado inválido, debe ser 'active' o 'inactive'"}), 400
        mechanic.status = data['status']
    for field in ('first_name', 'last_name', 'phone'):
        if field in data and data[field]:
            setattr(mechanic, field, data[field])

    base_repository.commit()
    return jsonify({'message': 'Mecánico actualizado'}), 200


def _serialize_mechanic(m):
    return {
        'user_id': m.user_id,
        'first_name': m.first_name,
        'last_name': m.last_name,
        'email': m.email,
        'phone': m.phone,
        'status': m.status
    }


def _serialize_business(b):
    return {
        'business_id': b.business_id,
        'business_name': b.business_name,
        'tax_id': b.tax_id,
        'address': b.address,
        'business_phone': b.business_phone,
        'business_registration_number': b.business_registration_number,
        'legal_documents_verified': b.legal_documents_verified
    }
