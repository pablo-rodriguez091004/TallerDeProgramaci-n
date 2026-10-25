"""Casos de uso de pagos simulados (deposito + saldo)."""

from domain.payments.entities import PAYMENT_METHODS
from domain.payments.ports import PaymentRepository
from domain.payments.rules import confirms_appointment
from domain.scheduling.ports import AppointmentRepository
from domain.scheduling.rules import ensure_participant
from domain.shared.errors import InvalidInput, NotFound, PermissionDenied
from domain.shared.ports import Clock, UnitOfWork


class PaymentService:

    def __init__(self, payments: PaymentRepository, appointments: AppointmentRepository,
                 uow: UnitOfWork, clock: Clock):
        self._payments = payments
        self._appointments = appointments
        self._uow = uow
        self._clock = clock

    def list_for_appointment(self, actor, appointment_id):
        appointment = self._appointments.get(appointment_id)
        if not appointment:
            raise NotFound('Cita no encontrada')
        ensure_participant(actor, appointment, 'No tienes permiso para ver estos pagos')
        return self._payments.list_by_appointment(appointment_id)

    def pay(self, actor, payment_id, payment_method=None):
        """
        Registra el pago (simulado, sin pasarela). Si es el DEPOSITO de una
        cita 'pending', la cita pasa a 'confirmed' en la misma transaccion.
        """
        payment = self._payments.get(payment_id)
        if not payment:
            raise NotFound('Pago no encontrado')

        appointment = self._appointments.get(payment.appointment_id)
        if actor.is_client and appointment.client_user_id != actor.user_id:
            raise PermissionDenied('No tienes permiso para pagar esto')
        if payment.is_completed:
            raise InvalidInput('Este pago ya fue completado')

        method = payment_method or payment.payment_method
        if method not in PAYMENT_METHODS:
            raise InvalidInput('Método de pago inválido')

        payment.complete(method, self._clock.now())
        self._payments.save(payment)
        if confirms_appointment(payment, appointment):
            appointment.status = 'confirmed'
            self._appointments.save(appointment)
        self._uow.commit()
        return payment
