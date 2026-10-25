"""PaymentService con repositorios, unit of work y RELOJ simulados."""

from unittest.mock import create_autospec

import pytest

from application.payments.services import PaymentService
from domain.payments.ports import PaymentRepository
from domain.scheduling.ports import AppointmentRepository
from domain.shared.errors import InvalidInput, NotFound, PermissionDenied
from domain.shared.ports import Clock, UnitOfWork
from tests.unit.factories import CLIENT, OTHER_CLIENT, OWNER, make_appointment, make_payment


@pytest.fixture
def deps(fixed_now):
    clock = create_autospec(Clock, instance=True)
    clock.now.return_value = fixed_now
    return {
        'payments': create_autospec(PaymentRepository, instance=True),
        'appointments': create_autospec(AppointmentRepository, instance=True),
        'uow': create_autospec(UnitOfWork, instance=True),
        'clock': clock,
    }


@pytest.fixture
def service(deps):
    return PaymentService(**deps)


def test_paying_the_deposit_completes_it_and_confirms_the_appointment(service, deps, fixed_now):
    deps['payments'].get.return_value = make_payment(payment_type='deposit')
    deps['appointments'].get.return_value = make_appointment(status='pending')

    payment = service.pay(CLIENT, 21, 'transfer')

    assert (payment.status, payment.payment_method, payment.paid_at) == ('completed', 'transfer', fixed_now)
    deps['payments'].save.assert_called_once_with(payment)
    [appointment] = deps['appointments'].save.call_args.args
    assert appointment.status == 'confirmed'
    deps['uow'].commit.assert_called_once_with()


def test_paying_the_balance_does_not_touch_the_appointment(service, deps):
    deps['payments'].get.return_value = make_payment(payment_type='balance', payment_method='card')
    deps['appointments'].get.return_value = make_appointment(status='confirmed')

    payment = service.pay(OWNER, 21)  # sin metodo: conserva el original

    assert payment.payment_method == 'card'
    deps['appointments'].save.assert_not_called()
    deps['uow'].commit.assert_called_once_with()


@pytest.mark.parametrize('actor, payment, method, error', [
    (CLIENT, make_payment(status='completed'), None, InvalidInput),
    (CLIENT, make_payment(), 'bitcoin', InvalidInput),
    (OTHER_CLIENT, make_payment(), None, PermissionDenied),
])
def test_invalid_payments_write_nothing(service, deps, actor, payment, method, error):
    deps['payments'].get.return_value = payment
    deps['appointments'].get.return_value = make_appointment()
    with pytest.raises(error):
        service.pay(actor, 21, method)
    deps['payments'].save.assert_not_called()
    deps['uow'].commit.assert_not_called()


def test_unknown_payment_is_not_found(service, deps):
    deps['payments'].get.return_value = None
    with pytest.raises(NotFound):
        service.pay(CLIENT, 404)
    deps['appointments'].get.assert_not_called()


def test_list_checks_that_the_actor_participates(service, deps):
    deps['appointments'].get.return_value = make_appointment()
    deps['payments'].list_by_appointment.return_value = [make_payment()]
    assert len(service.list_for_appointment(CLIENT, 7)) == 1
    with pytest.raises(PermissionDenied):
        service.list_for_appointment(OTHER_CLIENT, 7)
