from flask import Blueprint, jsonify

from api.auth import role_required
from api.deps import actor, container
from api.legacy import json_body, missing_field

service_bp = Blueprint('services', __name__)


@service_bp.route('', methods=['GET'])
def list_services():
    return jsonify([_serialize_service(s) for s in container().catalog.list_active()]), 200


@service_bp.route('/manage', methods=['GET'])
@role_required('owner', 'admin')
def list_services_for_management():
    """Catalogo completo del negocio, incluidos los servicios desactivados."""
    services = container().catalog.list_for_management(actor())
    return jsonify([_serialize_service(s) for s in services]), 200


@service_bp.route('', methods=['POST'])
@role_required('owner', 'admin')
def create_service():
    data = json_body()
    error = missing_field(data, ['service_name', 'estimated_duration_minutes', 'base_price'], allow_falsy=True)
    if error:
        return error
    service = container().catalog.create_basic(actor(), {
        'service_name': data['service_name'],
        'description': data.get('description'),
        'estimated_duration_minutes': data['estimated_duration_minutes'],
        'base_price': data['base_price'],
    })
    return jsonify({'message': 'Servicio creado', 'service_id': service.service_id}), 201


@service_bp.route('/<int:service_id>', methods=['PUT'])
@role_required('owner', 'admin')
def update_service(service_id):
    container().catalog.update_basic(service_id, json_body())
    return jsonify({'message': 'Servicio actualizado'}), 200


@service_bp.route('/<int:service_id>', methods=['DELETE'])
@role_required('owner', 'admin')
def deactivate_service(service_id):
    """Borrado logico: se marca status='inactive' (puede tener citas historicas)."""
    container().catalog.deactivate(service_id)
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
