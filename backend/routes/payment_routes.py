from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import current_user
from db.conexion import db
from models.payment_model import Payment
from models.appointment_model import Appointment
from middlewares.auth_middleware import role_required

payment_bp = Blueprint('payments', __name__)


@payment_bp.route('/appointment/<int:appointment_id>', methods=['GET'])
@role_required('client', 'mechanic', 'admin', 'owner')
def list_payments_for_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({'error': 'Cita no encontrada'}), 404

    if current_user.role == 'client' and appointment.client_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para ver estos pagos'}), 403

    payments = Payment.query.filter_by(appointment_id=appointment_id).all()
    return jsonify([_serialize_payment(p) for p in payments]), 200


@payment_bp.route('/<int:payment_id>/pay', methods=['POST'])
@role_required('client', 'admin', 'owner')
def pay(payment_id):
    """
    Simula el procesamiento de un pago (no hay pasarela real conectada).
    Si el pago que se completa es el DEPOSITO de una cita 'pending', la
    cita pasa automaticamente a 'confirmed' - asi el deposito es lo que
    confirma la cita, como se definio en la logica de negocio del proyecto.
    """
    payment = Payment.query.get(payment_id)
    if not payment:
        return jsonify({'error': 'Pago no encontrado'}), 404

    appointment = Appointment.query.get(payment.appointment_id)

    if current_user.role == 'client' and appointment.client_user_id != current_user.user_id:
        return jsonify({'error': 'No tienes permiso para pagar esto'}), 403

    if payment.status == 'completed':
        return jsonify({'error': 'Este pago ya fue completado'}), 400

    data = request.get_json(silent=True) or {}
    payment.payment_method = data.get('payment_method', payment.payment_method)
    payment.status = 'completed'
    payment.paid_at = datetime.utcnow()
    db.session.commit()

    if payment.payment_type == 'deposit' and appointment.status == 'pending':
        appointment.status = 'confirmed'
        db.session.commit()

    return jsonify({'message': 'Pago registrado (simulado)', 'payment_id': payment.payment_id}), 200


def _serialize_payment(p):
    return {
        'payment_id': p.payment_id,
        'appointment_id': p.appointment_id,
        'payment_type': p.payment_type,
        'payment_method': p.payment_method,
        'amount': p.amount,
        'status': p.status,
        'paid_at': p.paid_at.isoformat() if p.paid_at else None
    }
