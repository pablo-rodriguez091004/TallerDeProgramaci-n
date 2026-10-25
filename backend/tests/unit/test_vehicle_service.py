"""VehicleService en recepcion: el administrador registra vehiculos a nombre de un cliente."""

from unittest.mock import create_autospec

import pytest

from application.catalog.services import VehicleService
from domain.catalog.ports import VehicleRepository
from domain.identity.ports import UserRepository
from domain.shared.errors import InvalidInput, NotFound, PermissionDenied
from domain.shared.ports import UnitOfWork
from tests.unit.factories import ADMIN, CLIENT, OTHER_CLIENT, make_mechanic, make_vehicle

DATA = {'license_plate': 'NEW001', 'brand': 'Kia', 'model': 'Picanto', 'year': 2019, 'vehicle_type': 'car',
        'fuel_type': 'gasoline', 'transmission_type': 'manual'}


@pytest.fixture
def deps():
    deps = {'vehicles': create_autospec(VehicleRepository, instance=True),
            'users': create_autospec(UserRepository, instance=True),
            'uow': create_autospec(UnitOfWork, instance=True)}
    deps['vehicles'].get_by_plate.return_value = None
    deps['vehicles'].add.side_effect = lambda v: v
    deps['users'].get.side_effect = lambda user_id: make_mechanic(user_id=user_id, role='client') \
        if user_id == CLIENT.user_id else (make_mechanic(user_id=user_id) if user_id == 2 else None)
    return deps


def test_admin_registers_the_vehicle_for_the_client(deps):
    vehicle = VehicleService(**deps).register(ADMIN, DATA, client_user_id=CLIENT.user_id)
    assert vehicle.owner_user_id == CLIENT.user_id
    deps['uow'].commit.assert_called_once_with()


@pytest.mark.parametrize('client_user_id, error', [
    (None, InvalidInput),      # el admin debe indicar el cliente
    (999, NotFound),           # cliente inexistente
    (2, NotFound),             # el usuario 2 es mecanico, no cliente
])
def test_admin_needs_an_existing_client(deps, client_user_id, error):
    with pytest.raises(error):
        VehicleService(**deps).register(ADMIN, DATA, client_user_id=client_user_id)
    deps['vehicles'].add.assert_not_called()


def test_client_registers_for_himself_and_cannot_act_for_others(deps):
    service = VehicleService(**deps)
    assert service.register(CLIENT, DATA).owner_user_id == CLIENT.user_id
    with pytest.raises(PermissionDenied):
        service.list_mine(CLIENT, client_user_id=OTHER_CLIENT.user_id)
    deps['vehicles'].list_by_owner.return_value = [make_vehicle()]
    assert len(service.list_mine(ADMIN, client_user_id=CLIENT.user_id)) == 1
    deps['vehicles'].list_by_owner.assert_called_with(CLIENT.user_id)
