from flask import Blueprint, request, jsonify
from flask_login import current_user
from middlewares.auth_middleware import role_required
from repositories import base_repository, bay_repository, business_repository

bay_bp = Blueprint('bays', __name__)

VALID_STATUSES = ('available', 'under_maintenance')


@bay_bp.route('', methods=['GET'])
@role_required('owner', 'admin', 'mechanic')
def list_bays():
    business = business_repository.get_for_user(current_user)
    if not business:
        return jsonify({'error': 'No se encontró un negocio asociado'}), 404

    bays = bay_repository.list_by_business(business.business_id)
    return jsonify([_serialize_bay(b) for b in bays]), 200


@bay_bp.route('', methods=['POST'])
@role_required('owner', 'admin')
def create_bay():
    business = business_repository.get_for_user(current_user)
    if not business:
        return jsonify({'error': 'No se encontró un negocio asociado'}), 404

    data = request.get_json(silent=True) or {}
    if 'bay_number' not in data or not data['bay_number']:
        return jsonify({'error': 'El campo bay_number es obligatorio'}), 400

    if bay_repository.get_by_number(business.business_id, data['bay_number']):
        return jsonify({'error': 'Ya existe una bahía con ese número en este negocio'}), 409

    bay = bay_repository.create(
        business_id=business.business_id,
        bay_number=data['bay_number'],
        has_elevator=bool(data.get('has_elevator', False))
    )
    base_repository.commit()

    return jsonify({'message': 'Bahía creada', 'bay_id': bay.bay_id}), 201


@bay_bp.route('/<int:bay_id>', methods=['PUT'])
@role_required('owner', 'admin')
def update_bay(bay_id):
    bay = bay_repository.get_by_id(bay_id)
    if not bay:
        return jsonify({'error': 'Bahía no encontrada'}), 404

    data = request.get_json(silent=True) or {}
    if 'status' in data and data['status'] not in VALID_STATUSES:
        return jsonify({'error': f'Estado inválido, debe ser uno de: {VALID_STATUSES}'}), 400

    if 'has_elevator' in data:
        bay.has_elevator = bool(data['has_elevator'])
    if 'status' in data:
        bay.status = data['status']

    base_repository.commit()
    return jsonify({'message': 'Bahía actualizada'}), 200


def _serialize_bay(b):
    return {
        'bay_id': b.bay_id,
        'bay_number': b.bay_number,
        'has_elevator': b.has_elevator,
        'status': b.status
    }
