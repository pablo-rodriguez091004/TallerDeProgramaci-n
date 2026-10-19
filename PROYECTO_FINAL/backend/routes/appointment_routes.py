from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import current_user
from middlewares.auth_middleware import role_required
from repositories import base_repository, appointment_repository, payment_repository, \
    service_repository, vehicle_repository
from utils.scheduling_engine import find_bay_and_mechanic

appointment_bp = Blueprint('appointments', __name__)

# Porcentaje del precio del servicio que se cobra como deposito inicial.
# Es un valor de ejemplo (pago simulado) - ajustable segun la regla de
# negocio real que Pablo quiera definir para el proyecto.
DEPOSIT_PERCENTAGE = 0.3

VALID_STATUSES = ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled')
VALID_PAYMENT_METHODS = ('cash', 'card', 'transfer')


@appointment_bp.route('', methods=['POST'])
@role_required('client')
def create_appointment():
    """
    El cliente agenda una cita indicando: su vehiculo, el servicio deseado,
    y la hora de inicio. El backend calcula la hora de fin (segun la
    duracion estimada del servicio) y asigna automaticamente una bahia y
    un mecanico disponibles - el corazon del motor de agendamiento.
    """
    data = request.get_json(silent=True) or {}

    required_fields = ['vehicle_id', 'service_id', 'scheduled_start']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'El campo {field} es obligatorio'}), 400

    vehicle = vehicle_repository.get_by_id(data['vehicle_id'])
    if not vehicle or vehicle.owner_user_id != current_user.user_id:
        return jsonify({'error': 'Vehículo inválido'}), 400

    service = service_repository.get_by_id(data['service_id'])
    if not service or service.status != 'active':
        return jsonify({'error': 'Servicio inválido'}), 400

    try:
        scheduled_start = datetime.fromisoformat(data['scheduled_start'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Formato de scheduled_start inválido, usa ISO 8601 (ej. 2026-09-20T09:00:00)'}), 400

    metodo_pago = data.get('payment_method', 'cash')
    if metodo_pago not in VALID_PAYMENT_METHODS:
        return jsonify({'error': f'Método de pago inválido, debe ser uno de: {VALID_PAYMENT_METHODS}'}), 400

    scheduled_end = scheduled_start + timedelta(minutes=service.estimated_duration_minutes)

    bay, mechanic = find_bay_and_mechanic(service.business_id, scheduled_start, scheduled_end)
    if not bay or not mechanic:
        return jsonify({'error': 'No hay disponibilidad de bahía o mecánico en ese horario'}), 409

    appointment = appointment_repository.create(
        client_user_id=current_user.user_id,
        vehicle_id=vehicle.vehicle_id,
        service_id=service.service_id,
        bay_id=bay.bay_id,
        mechanic_user_id=mechanic.user_id,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        status='pending'
    )

    deposit_amount = round(service.base_price * DEPOSIT_PERCENTAGE)
    balance_amount = service.base_price - deposit_amount

    payment_repository.create(
        appointment_id=appointment.appointment_id,
        payment_type='deposit',
        payment_method=metodo_pago,
        amount=deposit_amount,
        status='pending'
    )
    payment_repository.create(
        appointment_id=appointment.appointment_id,
        payment_type='balance',
        payment_method=metodo_pago,
        amount=balance_amount,
        status='pending'
    )
    base_repository.commit()

    return jsonify({
        'message': 'Cita creada, pendiente de pago de depósito para confirmar',
        'appointment_id': appointment.appointment_id,
        'bay_id': bay.bay_id,
        'mechanic_user_id': mechanic.user_id,
        'scheduled_start': scheduled_start.isoformat(),
        'scheduled_end': scheduled_end.isoformat(),
        'deposit_amount': deposit_amount,
        'balance_amount': balance_amount
    }), 201


@appointment_bp.route('', methods=['GET'])
@role_required('client', 'mechanic', 'admin', 'owner')
def list_appointments():
    # El repositorio filtra segun el rol y carga cliente, mecanico, vehiculo,
    # servicio y bahia con joinedload (una sola consulta, sin N+1).
    appointments = appointment_repository.list_for_user(current_user)
    return jsonify([_serialize_appointment(a) for a in appointments]), 200


@appointment_bp.route('/<int:appointment_id>', methods=['GET'])
@role_required('client', 'mechanic', 'admin', 'owner')
def get_appointment(appointment_id):
    appointment = appointment_repository.get_detailed(appointment_id)
    if not appointment:
        return jsonify({'error': 'Cita no encontrada'}), 404

    if current_user.role == 'client' and appointment.client_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para ver esta cita'}), 403
    if current_user.role == 'mechanic' and appointment.mechanic_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para ver esta cita'}), 403

    return jsonify(_serialize_appointment(appointment)), 200


@appointment_bp.route('/<int:appointment_id>/status', methods=['PUT'])
@role_required('mechanic', 'admin', 'owner')
def update_status(appointment_id):
    appointment = appointment_repository.get_by_id(appointment_id)
    if not appointment:
        return jsonify({'error': 'Cita no encontrada'}), 404

    if current_user.role == 'mechanic' and appointment.mechanic_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para modificar esta cita'}), 403

    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    if new_status not in VALID_STATUSES:
        return jsonify({'error': f'Estado inválido, debe ser uno de: {VALID_STATUSES}'}), 400

    appointment.status = new_status
    base_repository.commit()

    return jsonify({'message': 'Estado de la cita actualizado', 'status': appointment.status}), 200


@appointment_bp.route('/<int:appointment_id>', methods=['DELETE'])
@role_required('client')
def cancel_appointment(appointment_id):
    appointment = appointment_repository.get_by_id(appointment_id)
    if not appointment:
        return jsonify({'error': 'Cita no encontrada'}), 404
    if appointment.client_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para cancelar esta cita'}), 403
    if appointment.status in ('completed', 'cancelled'):
        return jsonify({'error': 'Esta cita ya no se puede cancelar'}), 400

    appointment.status = 'cancelled'
    base_repository.commit()

    return jsonify({'message': 'Cita cancelada'}), 200


def _full_name(user):
    return f'{user.first_name} {user.last_name}' if user else None


def _serialize_appointment(a):
    return {
        'appointment_id': a.appointment_id,
        'client_user_id': a.client_user_id,
        'vehicle_id': a.vehicle_id,
        'service_id': a.service_id,
        'bay_id': a.bay_id,
        'mechanic_user_id': a.mechanic_user_id,
        'scheduled_start': a.scheduled_start.isoformat(),
        'scheduled_end': a.scheduled_end.isoformat(),
        'status': a.status,
        # Datos de las relaciones (ya cargados por joinedload en el listado)
        'client_name': _full_name(a.client),
        'mechanic_name': _full_name(a.mechanic),
        'vehicle_plate': a.vehicle.license_plate if a.vehicle else None,
        'service_name': a.service.service_name if a.service else None,
        'bay_number': a.bay.bay_number if a.bay else None
    }
