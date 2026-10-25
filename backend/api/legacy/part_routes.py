from flask import Blueprint, jsonify, request

from api.auth import role_required
from api.deps import actor, container
from api.legacy import json_body, missing_field

part_bp = Blueprint('parts', __name__)


@part_bp.route('', methods=['GET'])
@role_required('owner', 'admin', 'mechanic')
def list_parts():
    # ?include_inactive=1 solo tiene efecto para owner/admin (vista de gestion)
    include_inactive = request.args.get('include_inactive') == '1'
    parts = container().parts.list_for(actor(), include_inactive=include_inactive)
    return jsonify([_serialize_part(p) for p in parts]), 200


@part_bp.route('', methods=['POST'])
@role_required('owner', 'admin')
def create_part():
    data = json_body()
    error = missing_field(data, ['part_name', 'unit_price'], allow_falsy=True)
    if error:
        return error
    part = container().parts.create(actor(), data['part_name'], data['unit_price'], data.get('stock_quantity', 0))
    return jsonify({'message': 'Repuesto creado', 'part_id': part.part_id}), 201


@part_bp.route('/<int:part_id>', methods=['PUT'])
@role_required('owner', 'admin')
def update_part(part_id):
    container().parts.update(part_id, json_body())
    return jsonify({'message': 'Repuesto actualizado'}), 200


def _serialize_part(p):
    return {
        'part_id': p.part_id,
        'part_name': p.part_name,
        'unit_price': p.unit_price,
        'stock_quantity': p.stock_quantity,
        'status': p.status
    }
