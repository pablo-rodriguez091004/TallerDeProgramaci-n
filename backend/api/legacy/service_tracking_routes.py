from flask import Blueprint, jsonify

from api.auth import role_required
from api.deps import actor, container
from api.legacy import json_body

tracking_bp = Blueprint('tracking', __name__)


@tracking_bp.route('/appointment/<int:appointment_id>', methods=['GET'])
@role_required('client', 'mechanic', 'admin', 'owner')
def list_tracking(appointment_id):
    records = container().tracking.list_for(actor(), appointment_id)
    return jsonify([_serialize_tracking(r) for r in records]), 200


@tracking_bp.route('/appointment/<int:appointment_id>', methods=['POST'])
@role_required('mechanic', 'admin', 'owner')
def add_tracking(appointment_id):
    """El mecanico registra un paso del proceso y los repuestos usados (descuenta stock)."""
    data = json_body()
    record = container().tracking.record_step(
        actor(), appointment_id, data.get('status'), notes=data.get('notes'),
        current_mileage=data.get('current_mileage'), parts_used=data.get('parts_used', []))
    return jsonify({'message': 'Seguimiento registrado', 'tracking_id': record.tracking_id}), 201


def _serialize_tracking(t):
    return {
        'tracking_id': t.tracking_id,
        'status': t.status,
        'notes': t.notes,
        'current_mileage': t.current_mileage,
        'recorded_at': t.recorded_at.isoformat() if t.recorded_at else None,
        'parts_used': [
            {'part_id': u.part_id, 'part_name': u.part_name, 'quantity': u.quantity}
            for u in t.parts_used
        ]
    }
