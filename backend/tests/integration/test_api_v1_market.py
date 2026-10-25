"""
/api/v1/market de punta a punta (Flask + DuckDB). Las APIs externas se
sirven con las respuestas reales grabadas (httpx.MockTransport): ninguna
prueba sale a la red.
"""

import httpx
import pytest

from bootstrap import build_market_data
from infrastructure.persistence.unit_of_work import SystemClock
from tests.market_fixtures import fixture_handler

BASE = '/api/v1/market'


@pytest.fixture
def market(app, tmp_path, monkeypatch):
    """Reemplaza el MarketDataService del contenedor por uno con carpeta temporal y red simulada."""
    outage = {'datos.gov.co': False}

    def handler(request):
        if outage['datos.gov.co'] and request.url.host == 'www.datos.gov.co':
            return httpx.Response(503)
        return fixture_handler(request)

    config = {**app.config, 'MARKET_DATA_DIR': str(tmp_path), 'MARKET_RETRY_BASE_SECONDS': 0,
              'MARKET_MAX_RETRIES': 1}
    service = build_market_data(config, SystemClock(), transport=httpx.MockTransport(handler))
    monkeypatch.setattr(app.extensions['mecatrack'], 'market_data', service)
    return outage


def _assert_error(response, status, code):
    assert response.status_code == status, response.get_json()
    assert response.get_json()['code'] == code


def test_market_requires_owner_or_admin(app, login, market):
    _assert_error(app.test_client().get(f'{BASE}/sources'), 401, 'unauthorized')
    _assert_error(login('client@test.com').get(f'{BASE}/analytics/fleet-age'), 403, 'forbidden')
    _assert_error(login('mechanic@test.com').post(f'{BASE}/refresh'), 403, 'forbidden')


def test_analytics_before_refresh_returns_409(login, market):
    owner = login('owner@test.com')
    _assert_error(owner.get(f'{BASE}/analytics/motorization'), 409, 'market_data_not_loaded')
    sources = owner.get(f'{BASE}/sources').get_json()
    assert [s['fetched_at'] for s in sources['sources']] == [None, None, None]
    assert {c['name']: c['state'] for c in sources['circuits']} == {'datos.gov.co': 'CLOSED',
                                                                    'geoportal.dane.gov.co': 'CLOSED'}


def test_refresh_then_query_the_three_analytics(login, market):
    owner = login('owner@test.com')
    refresh = owner.post(f'{BASE}/refresh').get_json()
    assert [(r['source'], r['ok'], r['rows']) for r in refresh['results']] == [
        ('runt_fleet', True, 375), ('divipola', True, 12), ('dane_population', True, 12)]

    fleet = owner.get(f'{BASE}/analytics/fleet-age').get_json()
    assert {r['clase'] for r in fleet['rows']} == {'AUTOMOVIL', 'MOTOCICLETA', 'CAMIONETA'}
    assert {c['key'] for c in fleet['columns']} >= {'media', 'desviacion', 'mediana', 'p25', 'p75'}

    motorization = owner.get(f'{BASE}/analytics/motorization').get_json()
    assert {r['cod_dpto'] for r in motorization['rows']} == {'11', '91'}
    assert motorization['summary']['nacional_por_1000_hab'] > 0

    distribution = owner.get(f'{BASE}/analytics/age-distribution').get_json()
    assert distribution['summary']['rangos'] == ['0-4', '5-9', '10-14', '15-19', '20+']


def test_outage_opens_the_datos_gov_circuit_but_dane_still_works(login, market):
    owner = login('owner@test.com')
    assert all(r['ok'] for r in owner.post(f'{BASE}/refresh').get_json()['results'])

    market['datos.gov.co'] = True  # datos.gov.co empieza a responder 503
    body = owner.post(f'{BASE}/refresh').get_json()
    results = {r['source']: r for r in body['results']}
    circuits = {c['name']: c for c in body['circuits']}

    # RUNT: 2 intentos (1 + 1 reintento) -> 2 fallos; DIVIPOLA: 1 fallo mas -> 3 = umbral -> OPEN
    assert not results['runt_fleet']['ok'] and not results['divipola']['ok']
    assert circuits['datos.gov.co']['state'] == 'OPEN'
    assert circuits['datos.gov.co']['transitions'][-1]['to'] == 'OPEN'
    # El DANE tiene su propio breaker: sigue CLOSED y su descarga funciona
    assert results['dane_population']['ok'] and circuits['geoportal.dane.gov.co']['state'] == 'CLOSED'

    # Con el circuito abierto se rechaza sin llamar a la red
    again = {r['source']: r for r in owner.post(f'{BASE}/refresh').get_json()['results']}
    assert again['runt_fleet']['circuit_open'] and again['divipola']['circuit_open']

    # Los snapshots anteriores se conservan: el analisis sigue disponible
    assert owner.get(f'{BASE}/analytics/fleet-age').status_code == 200
