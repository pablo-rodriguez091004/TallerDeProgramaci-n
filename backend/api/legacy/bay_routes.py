from flask import Blueprint, jsonify

from api.auth import role_required
from api.deps import actor, container
from api.legacy import json_body, missing_field

bay_bp = Blueprint('bays', __name__)


@bay_bp.route('', methods=['GET'])
@role_required('owner', 'admin', 'mechanic')
def list_bays():
    return jsonify([_serialize_bay(b) for b in container().bays.list_for(actor())]), 200


@bay_bp.route('', methods=['POST'])
@role_required('owner', 'admin')
def create_bay():
    data = json_body()
    error = missing_field(data, ['bay_number'])
    if error:
        return error
    bay = container().bays.create(actor(), data['bay_number'], data.get('has_elevator', False))
    return jsonify({'message': 'Bahía creada', 'bay_id': bay.bay_id}), 201


@bay_bp.route('/<int:bay_id>', methods=['PUT'])
@role_required('owner', 'admin')
def update_bay(bay_id):
    container().bays.update(bay_id, json_body())
    return jsonify({'message': 'Bahía actualizada'}), 200


def _serialize_bay(b):
    return {
        'bay_id': b.bay_id,
        'bay_number': b.bay_number,
        'has_elevator': b.has_elevator,
        'status': b.status
    }
