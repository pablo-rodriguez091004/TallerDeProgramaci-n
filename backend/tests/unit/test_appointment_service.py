"""
AppointmentService con TODAS sus dependencias simuladas (unittest.mock).

Demuestra la testabilidad que da la inyeccion por constructor: sin Flask,
sin PostgreSQL y en milisegundos se verifica la orquestacion del caso de
uso (que se asigna, que se guarda, cuando se confirma la transaccion).
"""

from dataclasses import replace
from datetime import datetime
from unittest.mock import call, create_autospec

import pytest

from application.scheduling.services import AppointmentService
from domain.catalog.ports import ServiceRepository, VehicleRepository
from domain.payments.entities import Payment
from domain.payments.ports import PaymentRepository
from domain.scheduling.allocation import ResourceAllocator
from domain.scheduling.ports import AppointmentRepository
from domain.shared.errors import Conflict, InvalidInput, PermissionDenied
from domain.shared.ports import UnitOfWork
from tests.unit.factories import (CLIENT, MECHANIC, OTHER_CLIENT, START, make_appointment, make_bay, make_mechanic,
                                  make_service, make_vehicle)


@pytest.fixture
def deps():
    deps = {
        'appointments': create_autospec(AppointmentRepository, instance=True),
        'vehicles': create_autospec(VehicleRepository, instance=True),
        'services': create_autospec(ServiceRepository, instance=True),
        'allocator': create_autospec(ResourceAllocator, instance=True),
        'payments': create_autospec(PaymentRepository, instance=True),
        'uow': create_autospec(UnitOfWork, instance=True),
    }
    deps['vehicles'].get.return_value = make_vehicle()
    deps['services'].get.return_value = make_service()
    deps['allocator'].find_bay_and_mechanic.return_value = (make_bay(), make_mechanic())
    # El repositorio devuelve la cita con el id que asigna la BD.
    deps['appointments'].add.side_effect = lambda appointment: replace(appointment, appointment_id=7)
    return deps


@pytest.fixture
def service(deps):
    return AppointmentService(**deps)  # inyeccion por constructor


def test_book_assigns_resources_creates_two_payments_and_commits_once(service, deps):
    booking = service.book(CLIENT, vehicle_id=10, service_id=1, scheduled_start=START, payment_method='card')

    end = datetime(2030, 1, 10, 9, 45)  # inicio + 45 min del servicio
    deps['allocator'].find_bay_and_mechanic.assert_called_once_with(1, START, end)

    [stored] = deps['appointments'].add.call_args.args
    assert (stored.client_user_id, stored.bay_id, stored.mechanic_user_id) == (CLIENT.user_id, 1, MECHANIC.user_id)
    assert (stored.scheduled_end, stored.status) == (end, 'pending')

    assert deps['payments'].add.call_args_list == [
        call(Payment(appointment_id=7, payment_type='deposit', payment_method='card', amount=24000)),
        call(Payment(appointment_id=7, payment_type='balance', payment_method='card', amount=56000)),
    ]
    deps['uow'].commit.assert_called_once_with()
    assert (booking.appointment.appointment_id, booking.deposit_amount, booking.balance_amount) == (7, 24000, 56000)


def test_book_without_availability_raises_conflict_and_writes_nothing(service, deps):
    deps['allocator'].find_bay_and_mechanic.return_value = (None, None)

    with pytest.raises(Conflict) as error:
        service.book(CLIENT, 10, 1, START)

    assert error.value.message == 'No hay disponibilidad de bahía o mecánico en ese horario'
    deps['appointments'].add.assert_not_called()
    deps['payments'].add.assert_not_called()
    deps['uow'].commit.assert_not_called()


@pytest.mark.parametrize('setup, message', [
    (lambda d: setattr(d['vehicles'].get, 'return_value', make_vehicle(owner_user_id=OTHER_CLIENT.user_id)),
     'Vehículo inválido'),
    (lambda d: setattr(d['vehicles'].get, 'return_value', None), 'Vehículo inválido'),
    (lambda d: setattr(d['services'].get, 'return_value', make_service(status='inactive')), 'Servicio inválido'),
])
def test_book_validates_before_looking_for_resources(service, deps, setup, message):
    setup(deps)
    with pytest.raises(InvalidInput, match=message):
        service.book(CLIENT, 10, 1, START)
    deps['allocator'].find_bay_and_mechanic.assert_not_called()


def test_book_rejects_unknown_payment_method(service, deps):
    with pytest.raises(InvalidInput, match='Método de pago inválido'):
        service.book(CLIENT, 10, 1, START, payment_method='bitcoin')
    deps['uow'].commit.assert_not_called()


def test_cancel_marks_cancelled_and_saves(service, deps):
    deps['appointments'].get.return_value = make_appointment(status='confirmed')
    service.cancel(CLIENT, 7)
    [saved] = deps['appointments'].save.call_args.args
    assert saved.status == 'cancelled'
    deps['uow'].commit.assert_called_once_with()


@pytest.mark.parametrize('actor, status, error', [
    (OTHER_CLIENT, 'pending', PermissionDenied),
    (CLIENT, 'completed', InvalidInput),
    (CLIENT, 'cancelled', InvalidInput),
])
def test_cancel_rules(service, deps, actor, status, error):
    deps['appointments'].get.return_value = make_appointment(status=status)
    with pytest.raises(error):
        service.cancel(actor, 7)
    deps['appointments'].save.assert_not_called()


def test_mechanic_cannot_change_status_of_an_appointment_assigned_to_someone_else(service, deps):
    deps['appointments'].get.return_value = make_appointment(mechanic_user_id=555)
    with pytest.raises(PermissionDenied):
        service.change_status(MECHANIC, 7, 'completed')
    deps['uow'].commit.assert_not_called()


def test_autospec_mocks_enforce_the_port_contract(deps):
    """
    Un Mock() comun acepta cualquier metodo y ocultaria errores de interfaz.
    create_autospec solo acepta lo que declara el puerto y con su firma.
    """
    with pytest.raises(AttributeError):
        deps['appointments'].find_all()  # AppointmentRepository no declara find_all
    with pytest.raises(TypeError):
        deps['payments'].add()  # add(payment) exige un argumento
