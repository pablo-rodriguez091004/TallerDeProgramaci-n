from flask import Blueprint, request, jsonify
from flask_login import current_user
from middlewares.auth_middleware import role_required
from repositories import base_repository, appointment_repository, part_repository, \
    service_tracking_repository

tracking_bp = Blueprint('tracking', __name__)

VALID_STATUSES = ('received', 'diagnosing', 'in_repair', 'quality_check', 'ready_for_pickup', 'delivered')


@tracking_bp.route('/appointment/<int:appointment_id>', methods=['GET'])
@role_required('client', 'mechanic', 'admin', 'owner')
def list_tracking(appointment_id):
    appointment = appointment_repository.get_by_id(appointment_id)
    if not appointment:
        return jsonify({'error': 'Cita no encontrada'}), 404

    if current_user.role == 'client' and appointment.client_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para ver este seguimiento'}), 403
    if current_user.role == 'mechanic' and appointment.mechanic_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para ver este seguimiento'}), 403

    records = service_tracking_repository.list_by_appointment(appointment_id)
    return jsonify([_serialize_tracking(r) for r in records]), 200


@tracking_bp.route('/appointment/<int:appointment_id>', methods=['POST'])
@role_required('mechanic', 'admin', 'owner')
def add_tracking(appointment_id):
    """
    El mecanico registra un nuevo paso del proceso (ej. 'diagnosing',
    'in_repair'), con observaciones opcionales y, si aplica, los repuestos
    usados en ese paso - lo que descuenta stock automaticamente.
    """
    appointment = appointment_repository.get_by_id(appointment_id)
    if not appointment:
        return jsonify({'error': 'Cita no encontrada'}), 404

    if current_user.role == 'mechanic' and appointment.mechanic_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para actualizar esta cita'}), 403

    data = request.get_json(silent=True) or {}
    if data.get('status') not in VALID_STATUSES:
        return jsonify({'error': f'Estado inválido, debe ser uno de: {VALID_STATUSES}'}), 400

    tracking = service_tracking_repository.create(
        appointment_id=appointment_id,
        status=data['status'],
        notes=data.get('notes'),
        current_mileage=data.get('current_mileage')
    )

    parts_used = data.get('parts_used', [])
    for item in parts_used:
        part = part_repository.get_by_id(item.get('part_id'))
        quantity = item.get('quantity', 1)

        if not part:
            base_repository.rollback()
            return jsonify({'error': f"Repuesto {item.get('part_id')} no encontrado"}), 400
        if not isinstance(quantity, int) or quantity < 1:
            base_repository.rollback()
            return jsonify({'error': 'La cantidad de cada repuesto debe ser un entero mayor a 0'}), 400
        if part.stock_quantity < quantity:
            base_repository.rollback()
            return jsonify({'error': f'No hay stock suficiente de {part.part_name}'}), 400

        part.stock_quantity -= quantity
        service_tracking_repository.add_part_usage(tracking.tracking_id, part.part_id, quantity)

    base_repository.commit()

    return jsonify({'message': 'Seguimiento registrado', 'tracking_id': tracking.tracking_id}), 201


def _serialize_tracking(t):
    return {
        'tracking_id': t.tracking_id,
        'status': t.status,
        'notes': t.notes,
        'current_mileage': t.current_mileage,
        'recorded_at': t.recorded_at.isoformat() if t.recorded_at else None,
        'parts_used': [
            {'part_id': u.part_id, 'part_name': u.part.part_name, 'quantity': u.quantity}
            for u in t.parts_used
        ]
    }
