from flask import Blueprint, request, jsonify
from flask_login import current_user
from middlewares.auth_middleware import role_required
from repositories import base_repository, business_repository, part_repository

part_bp = Blueprint('parts', __name__)


@part_bp.route('', methods=['GET'])
@role_required('owner', 'admin', 'mechanic')
def list_parts():
    business = business_repository.get_for_user(current_user)
    if not business:
        return jsonify({'error': 'No se encontró un negocio asociado'}), 404

    # ?include_inactive=1 solo tiene efecto para owner/admin (vista de gestion)
    include_inactive = request.args.get('include_inactive') == '1' and current_user.role in ('owner', 'admin')
    parts = part_repository.list_by_business(business.business_id, include_inactive=include_inactive)
    return jsonify([_serialize_part(p) for p in parts]), 200


@part_bp.route('', methods=['POST'])
@role_required('owner', 'admin')
def create_part():
    business = business_repository.get_for_user(current_user)
    if not business:
        return jsonify({'error': 'No se encontró un negocio asociado'}), 404

    data = request.get_json(silent=True) or {}
    required_fields = ['part_name', 'unit_price']
    for field in required_fields:
        if field not in data or data[field] in (None, ''):
            return jsonify({'error': f'El campo {field} es obligatorio'}), 400

    part = part_repository.create(
        business_id=business.business_id,
        part_name=data['part_name'],
        unit_price=data['unit_price'],
        stock_quantity=data.get('stock_quantity', 0)
    )
    base_repository.commit()

    return jsonify({'message': 'Repuesto creado', 'part_id': part.part_id}), 201


@part_bp.route('/<int:part_id>', methods=['PUT'])
@role_required('owner', 'admin')
def update_part(part_id):
    part = part_repository.get_by_id(part_id)
    if not part:
        return jsonify({'error': 'Repuesto no encontrado'}), 404

    data = request.get_json(silent=True) or {}
    if 'status' in data and data['status'] not in ('active', 'inactive'):
        return jsonify({'error': "Estado inválido, debe ser 'active' o 'inactive'"}), 400

    editable_fields = ['part_name', 'unit_price', 'stock_quantity', 'status']
    for field in editable_fields:
        if field in data:
            setattr(part, field, data[field])

    base_repository.commit()
    return jsonify({'message': 'Repuesto actualizado'}), 200


def _serialize_part(p):
    return {
        'part_id': p.part_id,
        'part_name': p.part_name,
        'unit_price': p.unit_price,
        'stock_quantity': p.stock_quantity,
        'status': p.status
    }
