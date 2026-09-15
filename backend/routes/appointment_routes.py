from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import current_user
from db.conexion import db
from models.appointment_model import Appointment
from models.vehicle_model import Vehicle
from models.service_model import Service
from models.payment_model import Payment
from middlewares.auth_middleware import role_required
from utils.scheduling_engine import find_bay_and_mechanic

appointment_bp = Blueprint('appointments', __name__)

# Porcentaje del precio del servicio que se cobra como deposito inicial.
# Es un valor de ejemplo (pago simulado) - ajustable segun la regla de
# negocio real que Pablo quiera definir para el proyecto.
DEPOSIT_PERCENTAGE = 0.3


@appointment_bp.route('', methods=['POST'])
@role_required('client')
def create_appointment():
    """
    El cliente agenda una cita indicando: su vehiculo, el servicio deseado,
    y la hora de inicio. El backend calcula la hora de fin (segun la
    duracion estimada del servicio) y asigna automaticamente una bahia y
    un mecanico disponibles - el corazon del motor de agendamiento.
    """
    data = request.get_json()

    required_fields = ['vehicle_id', 'service_id', 'scheduled_start']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'El campo {field} es obligatorio'}), 400

    vehicle = Vehicle.query.get(data['vehicle_id'])
    if not vehicle or vehicle.owner_user_id != current_user.user_id:
        return jsonify({'error': 'Vehículo inválido'}), 400

    service = Service.query.get(data['service_id'])
    if not service or service.status != 'active':
        return jsonify({'error': 'Servicio inválido'}), 400

    try:
        scheduled_start = datetime.fromisoformat(data['scheduled_start'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Formato de scheduled_start inválido, usa ISO 8601 (ej. 2026-09-20T09:00:00)'}), 400

    scheduled_end = scheduled_start + timedelta(minutes=service.estimated_duration_minutes)

    bay, mechanic = find_bay_and_mechanic(service.business_id, scheduled_start, scheduled_end)
    if not bay or not mechanic:
        return jsonify({'error': 'No hay disponibilidad de bahía o mecánico en ese horario'}), 409

    appointment = Appointment(
        client_user_id=current_user.user_id,
        vehicle_id=vehicle.vehicle_id,
        service_id=service.service_id,
        bay_id=bay.bay_id,
        mechanic_user_id=mechanic.user_id,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        status='pending'
    )
    db.session.add(appointment)
    db.session.flush()  # asigna appointment_id sin cerrar la transaccion

    deposit_amount = round(service.base_price * DEPOSIT_PERCENTAGE)
    balance_amount = service.base_price - deposit_amount
    metodo_pago = data.get('payment_method', 'cash')

    deposit = Payment(
        appointment_id=appointment.appointment_id,
        payment_type='deposit',
        payment_method=metodo_pago,
        amount=deposit_amount,
        status='pending'
    )
    balance = Payment(
        appointment_id=appointment.appointment_id,
        payment_type='balance',
        payment_method=metodo_pago,
        amount=balance_amount,
        status='pending'
    )
    db.session.add_all([deposit, balance])
    db.session.commit()

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
    """
    Cada rol ve un subconjunto distinto:
    - cliente: solo sus propias citas.
    - mecanico: solo las citas que tiene asignadas.
    - admin/owner: todas las citas del sistema.
    """
    if current_user.role == 'client':
        appointments = Appointment.query.filter_by(client_user_id=current_user.user_id).all()
    elif current_user.role == 'mechanic':
        appointments = Appointment.query.filter_by(mechanic_user_id=current_user.user_id).all()
    else:
        appointments = Appointment.query.all()

    return jsonify([_serialize_appointment(a) for a in appointments]), 200


@appointment_bp.route('/<int:appointment_id>', methods=['GET'])
@role_required('client', 'mechanic', 'admin', 'owner')
def get_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
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
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({'error': 'Cita no encontrada'}), 404

    if current_user.role == 'mechanic' and appointment.mechanic_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para modificar esta cita'}), 403

    data = request.get_json()
    new_status = data.get('status')
    valid_statuses = ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled')
    if new_status not in valid_statuses:
        return jsonify({'error': f'Estado inválido, debe ser uno de: {valid_statuses}'}), 400

    appointment.status = new_status
    db.session.commit()

    return jsonify({'message': 'Estado de la cita actualizado', 'status': appointment.status}), 200


@appointment_bp.route('/<int:appointment_id>', methods=['DELETE'])
@role_required('client')
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({'error': 'Cita no encontrada'}), 404
    if appointment.client_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para cancelar esta cita'}), 403
    if appointment.status in ('completed', 'cancelled'):
        return jsonify({'error': 'Esta cita ya no se puede cancelar'}), 400

    appointment.status = 'cancelled'
    db.session.commit()

    return jsonify({'message': 'Cita cancelada'}), 200


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
        'status': a.status
    }
