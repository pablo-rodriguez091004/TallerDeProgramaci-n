from flask import Blueprint, request, jsonify
from flask_login import current_user
from db.conexion import db
from models.appointment_model import Appointment
from models.service_tracking_model import ServiceTracking
from models.service_tracking_parts_model import ServiceTrackingPart
from models.part_model import Part
from middlewares.auth_middleware import role_required

tracking_bp = Blueprint('tracking', __name__)


@tracking_bp.route('/appointment/<int:appointment_id>', methods=['GET'])
@role_required('client', 'mechanic', 'admin', 'owner')
def list_tracking(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({'error': 'Cita no encontrada'}), 404

    if current_user.role == 'client' and appointment.client_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para ver este seguimiento'}), 403
    if current_user.role == 'mechanic' and appointment.mechanic_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para ver este seguimiento'}), 403

    records = ServiceTracking.query.filter_by(appointment_id=appointment_id).order_by(ServiceTracking.recorded_at).all()
    return jsonify([_serialize_tracking(r) for r in records]), 200


@tracking_bp.route('/appointment/<int:appointment_id>', methods=['POST'])
@role_required('mechanic', 'admin', 'owner')
def add_tracking(appointment_id):
    """
    El mecanico registra un nuevo paso del proceso (ej. 'diagnosing',
    'in_repair'), con observaciones opcionales y, si aplica, los repuestos
    usados en ese paso - lo que descuenta stock automaticamente.
    """
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({'error': 'Cita no encontrada'}), 404

    if current_user.role == 'mechanic' and appointment.mechanic_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para actualizar esta cita'}), 403

    data = request.get_json()
    valid_statuses = ('received', 'diagnosing', 'in_repair', 'quality_check', 'ready_for_pickup', 'delivered')
    if data.get('status') not in valid_statuses:
        return jsonify({'error': f'Estado inválido, debe ser uno de: {valid_statuses}'}), 400

    tracking = ServiceTracking(
        appointment_id=appointment_id,
        status=data['status'],
        notes=data.get('notes'),
        current_mileage=data.get('current_mileage')
    )
    db.session.add(tracking)
    db.session.flush()

    parts_used = data.get('parts_used', [])
    for item in parts_used:
        part = Part.query.get(item.get('part_id'))
        quantity = item.get('quantity', 1)

        if not part:
            db.session.rollback()
            return jsonify({'error': f"Repuesto {item.get('part_id')} no encontrado"}), 400
        if part.stock_quantity < quantity:
            db.session.rollback()
            return jsonify({'error': f'No hay stock suficiente de {part.part_name}'}), 400

        part.stock_quantity -= quantity
        db.session.add(ServiceTrackingPart(
            tracking_id=tracking.tracking_id,
            part_id=part.part_id,
            quantity=quantity
        ))

    db.session.commit()

    return jsonify({'message': 'Seguimiento registrado', 'tracking_id': tracking.tracking_id}), 201


def _serialize_tracking(t):
    return {
        'tracking_id': t.tracking_id,
        'status': t.status,
        'notes': t.notes,
        'current_mileage': t.current_mileage,
        'recorded_at': t.recorded_at.isoformat() if t.recorded_at else None
    }
