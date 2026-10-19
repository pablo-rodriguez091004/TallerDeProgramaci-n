from flask import Blueprint, request, jsonify
from flask_login import current_user
from middlewares.auth_middleware import role_required
from repositories import base_repository, business_repository, service_repository

service_bp = Blueprint('services', __name__)


@service_bp.route('', methods=['GET'])
def list_services():
    services = service_repository.list_active()
    return jsonify([_serialize_service(s) for s in services]), 200


@service_bp.route('/manage', methods=['GET'])
@role_required('owner', 'admin')
def list_services_for_management():
    """Catalogo completo del negocio, incluidos los servicios desactivados."""
    business = business_repository.get_for_user(current_user)
    if not business:
        return jsonify({'error': 'No se encontró un negocio asociado'}), 404

    services = service_repository.list_by_business(business.business_id)
    return jsonify([_serialize_service(s) for s in services]), 200


@service_bp.route('', methods=['POST'])
@role_required('owner', 'admin')
def create_service():
    business = business_repository.get_for_user(current_user)
    if not business:
        return jsonify({'error': 'No se encontró un negocio asociado'}), 404

    data = request.get_json(silent=True) or {}
    required_fields = ['service_name', 'estimated_duration_minutes', 'base_price']
    for field in required_fields:
        if field not in data or data[field] in (None, ''):
            return jsonify({'error': f'El campo {field} es obligatorio'}), 400

    service = service_repository.create(
        business_id=business.business_id,
        service_name=data['service_name'],
        description=data.get('description'),
        estimated_duration_minutes=data['estimated_duration_minutes'],
        base_price=data['base_price']
    )
    base_repository.commit()

    return jsonify({'message': 'Servicio creado', 'service_id': service.service_id}), 201


@service_bp.route('/<int:service_id>', methods=['PUT'])
@role_required('owner', 'admin')
def update_service(service_id):
    service = service_repository.get_by_id(service_id)
    if not service:
        return jsonify({'error': 'Servicio no encontrado'}), 404

    data = request.get_json(silent=True) or {}
    if 'status' in data and data['status'] not in ('active', 'inactive'):
        return jsonify({'error': "Estado inválido, debe ser 'active' o 'inactive'"}), 400

    editable_fields = ['service_name', 'description', 'estimated_duration_minutes', 'base_price', 'status']
    for field in editable_fields:
        if field in data:
            setattr(service, field, data[field])

    base_repository.commit()
    return jsonify({'message': 'Servicio actualizado'}), 200


@service_bp.route('/<int:service_id>', methods=['DELETE'])
@role_required('owner', 'admin')
def deactivate_service(service_id):
    """
    No se borra fisicamente el servicio (podria tener citas historicas
    asociadas por FK) - se desactiva marcando status='inactive'.
    """
    service = service_repository.get_by_id(service_id)
    if not service:
        return jsonify({'error': 'Servicio no encontrado'}), 404

    service.status = 'inactive'
    base_repository.commit()
    return jsonify({'message': 'Servicio desactivado'}), 200


def _serialize_service(s):
    return {
        'service_id': s.service_id,
        'service_name': s.service_name,
        'description': s.description,
        'estimated_duration_minutes': s.estimated_duration_minutes,
        'base_price': s.base_price,
        'status': s.status
    }
