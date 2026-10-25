"""TrackingService: el descuento de stock es todo o nada."""

from dataclasses import replace
from unittest.mock import create_autospec

import pytest

from application.tracking.services import TrackingService
from domain.catalog.ports import PartRepository
from domain.scheduling.ports import AppointmentRepository
from domain.shared.errors import InvalidInput
from domain.shared.ports import UnitOfWork
from domain.tracking.ports import TrackingRepository
from tests.unit.factories import MECHANIC, make_appointment, make_part


@pytest.fixture
def deps():
    deps = {
        'appointments': create_autospec(AppointmentRepository, instance=True),
        'tracking': create_autospec(TrackingRepository, instance=True),
        'parts': create_autospec(PartRepository, instance=True),
        'uow': create_autospec(UnitOfWork, instance=True),
    }
    deps['appointments'].get.return_value = make_appointment()
    stock = {5: make_part(part_id=5, stock_quantity=5), 6: make_part(part_id=6, part_name='Filtro', stock_quantity=1)}
    deps['parts'].get.side_effect = lambda part_id: replace(stock[part_id]) if part_id in stock else None
    deps['tracking'].add.side_effect = lambda record: replace(record, tracking_id=1)
    return deps


def test_records_step_and_discounts_stock(deps):
    record = TrackingService(**deps).record_step(MECHANIC, 7, 'in_repair', parts_used=[
        {'part_id': 5, 'quantity': 2}, {'part_id': 6}])

    saved = {p.part_id: p.stock_quantity for (p,), _ in deps['parts'].save.call_args_list}
    assert saved == {5: 3, 6: 0}
    assert [(u.part_id, u.quantity) for u in record.parts_used] == [(5, 2), (6, 1)]
    deps['uow'].commit.assert_called_once_with()


def test_if_one_part_fails_nothing_is_saved(deps):
    with pytest.raises(InvalidInput, match='No hay stock suficiente de Filtro'):
        TrackingService(**deps).record_step(MECHANIC, 7, 'in_repair', parts_used=[
            {'part_id': 5, 'quantity': 2}, {'part_id': 6, 'quantity': 2}])

    deps['parts'].save.assert_not_called()
    deps['tracking'].add.assert_not_called()
    deps['uow'].commit.assert_not_called()
