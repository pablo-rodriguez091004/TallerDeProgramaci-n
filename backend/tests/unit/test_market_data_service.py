"""MarketDataService con fuentes, almacenamiento y monitor simulados."""

from datetime import datetime
from unittest.mock import create_autospec

from application.market_data.services import MarketDataService
from domain.market_data.errors import DataSourceUnavailable
from domain.market_data.ports import (DataSource, HealthMonitor, PopulationSource, Snapshot, SnapshotStore,
                                      SourceInfo, VehicleFleetSource)
from domain.shared.ports import Clock


def source(spec, key):
    mock = create_autospec(spec, instance=True)
    mock.info = SourceInfo(key, key.title(), 'test', f'https://example/{key}')
    return mock


def test_one_failing_source_does_not_stop_the_others(fixed_now):
    fleet, population = source(VehicleFleetSource, 'runt_fleet'), source(PopulationSource, 'dane_population')
    fleet.fetch.return_value = [{'vehiculos': '1'}, {'vehiculos': '2'}]
    population.fetch.side_effect = DataSourceUnavailable('dane_population', 'circuit OPEN', circuit_open=True)
    store = create_autospec(SnapshotStore, instance=True)
    store.save.side_effect = lambda key, records, at: Snapshot(key, at, len(records), f'/tmp/{key}.json')
    clock = create_autospec(Clock, instance=True)
    clock.now.return_value = fixed_now
    ticks = iter([0.0, 1.25, 2.0, 2.01])

    results = MarketDataService([fleet, population], store, create_autospec(HealthMonitor, instance=True), clock,
                                timer=lambda: next(ticks)).refresh()

    assert [(r.source, r.ok, r.rows, r.elapsed_ms) for r in results] == [
        ('runt_fleet', True, 2, 1250), ('dane_population', False, None, 10)]
    assert results[1].circuit_open and results[1].error == 'circuit OPEN'
    store.save.assert_called_once_with('runt_fleet', [{'vehiculos': '1'}, {'vehiculos': '2'}], fixed_now)


def test_snapshots_and_health_are_read_from_the_ports():
    fleet = source(DataSource, 'runt_fleet')
    store = create_autospec(SnapshotStore, instance=True)
    store.latest.return_value = Snapshot('runt_fleet', datetime(2030, 1, 1), 10, '/tmp/x.json')
    health = create_autospec(HealthMonitor, instance=True)
    health.health.return_value = []
    service = MarketDataService([fleet], store, health, create_autospec(Clock, instance=True))
    assert service.snapshots()['runt_fleet'].rows == 10
    assert service.health() == []
