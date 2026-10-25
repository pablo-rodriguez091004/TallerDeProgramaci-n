"""
Transporte httpx que sirve las respuestas REALES grabadas en
tests/fixtures/market (ver README.json): datos.gov.co (RUNT y DIVIPOLA) y
el geoportal del DANE. Permite ejercitar el flujo completo sin red.
"""

import json
from pathlib import Path

import httpx

FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'market'


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding='utf-8'))


def fixture_handler(request):
    path = request.url.path
    if request.url.host == 'www.datos.gov.co' and path.endswith('/u3vn-bdcy.json'):
        return httpx.Response(200, json=load('runt_fleet_sample.json'))
    if request.url.host == 'www.datos.gov.co' and path.endswith('/gdxc-w37w.json'):
        return httpx.Response(200, json=load('divipola_sample.json'))
    if request.url.host == 'geoportal.dane.gov.co' and path.endswith('/MapServer/4/query'):
        return httpx.Response(200, json=load('dane_population_sample.json'))
    return httpx.Response(404, json={'error': f'no fixture for {request.url}'})


def fixture_transport():
    return httpx.MockTransport(fixture_handler)
