from flask import Blueprint, jsonify

from api.auth import role_required
from api.deps import actor, container
from api.legacy import json_body

payment_bp = Blueprint('payments', __name__)


@payment_bp.route('/appointment/<int:appointment_id>', methods=['GET'])
@role_required('client', 'mechanic', 'admin', 'owner')
def list_payments_for_appointment(appointment_id):
    payments = container().payments.list_for_appointment(actor(), appointment_id)
    return jsonify([_serialize_payment(p) for p in payments]), 200


@payment_bp.route('/<int:payment_id>/pay', methods=['POST'])
@role_required('client', 'admin', 'owner')
def pay(payment_id):
    """Pago simulado; pagar el deposito confirma la cita (ver PaymentService.pay)."""
    payment = container().payments.pay(actor(), payment_id, json_body().get('payment_method'))
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
