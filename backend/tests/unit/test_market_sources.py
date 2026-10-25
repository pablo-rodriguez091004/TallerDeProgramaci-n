"""
Adaptadores de datos.gov.co y del geoportal del DANE contra respuestas
REALES grabadas (tests/fixtures/market, ver README.json) servidas por
httpx.MockTransport: se prueba el parseo y la paginacion sin red.
"""

import json
from pathlib import Path

import httpx
import pytest

from domain.market_data.errors import DataSourceUnavailable
from infrastructure.market_data.clients import DanePopulationSource, DivipolaSource, RuntFleetSource, SocrataClient
from infrastructure.resilience.circuit_breaker import CircuitBreaker
from infrastructure.resilience.http_client import ResilientHttpClient, TransientHttpError
from infrastructure.resilience.retry import RetryPolicy

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures' / 'market'


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding='utf-8'))


def http(handler, threshold=3):
    breaker = CircuitBreaker('test', failure_threshold=threshold, failure_exceptions=(TransientHttpError,))
    return ResilientHttpClient(breaker, RetryPolicy(max_retries=1, base_delay=0, retry_on=(TransientHttpError,)),
                               transport=httpx.MockTransport(handler), sleep=lambda s: None)


def test_runt_source_sends_the_aggregated_soql_and_returns_real_rows():
    rows = load('runt_fleet_sample.json')
    seen = []

    def handler(request):
        seen.append(dict(request.url.params))
        return httpx.Response(200, json=rows)

    result = RuntFleetSource(SocrataClient(http(handler))).fetch()

    assert result == rows and len(result) == 375
    assert set(result[0]) == {'nombre_departamento', 'nombre_de_la_clase', 'fecha_de_registro', 'vehiculos',
                              'mes_publicacion', 'anio_publicacion'}
    assert "estado_del_vehiculo = 'ACTIVO'" in seen[0]['$where'] and 'sum(cantidad)' in seen[0]['$select']


def test_socrata_paginates_until_a_short_page():
    rows = load('divipola_sample.json')  # 12 filas reales
    offsets = []

    def handler(request):
        offset, limit = int(request.url.params['$offset']), int(request.url.params['$limit'])
        offsets.append(offset)
        return httpx.Response(200, json=rows[offset:offset + limit])

    result = DivipolaSource(SocrataClient(http(handler), page_size=5)).fetch()
    assert result == rows and offsets == [0, 5, 10]


def test_dane_population_parses_arcgis_features_and_paginates():
    data = load('dane_population_sample.json')
    features = data['features']

    def handler(request):
        offset = int(request.url.params['resultOffset'])
        page = features[offset:offset + 8]
        return httpx.Response(200, json={'features': page, 'exceededTransferLimit': offset + 8 < len(features)})

    result = DanePopulationSource(http(handler), page_size=8).fetch()
    assert len(result) == len(features) == 12
    bogota = next(r for r in result if r['cod_mpio'] == '11001')
    assert set(bogota) == {'cod_dpto', 'cod_mpio', 'municipio', 'poblacion'}
    assert bogota['poblacion'] > 7_000_000


def test_arcgis_error_inside_http_200_becomes_data_source_unavailable():
    handler = lambda request: httpx.Response(200, json={'error': {'code': 400, 'message': 'Invalid query'}})
    with pytest.raises(DataSourceUnavailable) as error:
        DanePopulationSource(http(handler)).fetch()
    assert error.value.source == 'dane_population' and not error.value.circuit_open


def test_open_circuit_is_reported_as_circuit_open():
    client = http(lambda request: httpx.Response(503), threshold=2)
    source = RuntFleetSource(SocrataClient(client))
    with pytest.raises(DataSourceUnavailable):
        source.fetch()  # 2 fallos -> se abre
    with pytest.raises(DataSourceUnavailable) as error:
        source.fetch()
    assert error.value.circuit_open
