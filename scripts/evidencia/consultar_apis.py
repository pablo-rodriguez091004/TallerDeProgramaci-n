"""
Consulta REAL a las APIs colombianas con el cliente resiliente del proyecto
y muestra la respuesta JSON recortada (las primeras filas + el total).

    backend/venv/bin/python scripts/evidencia/consultar_apis.py datos.gov.co
    backend/venv/bin/python scripts/evidencia/consultar_apis.py dane
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'backend'))

from infrastructure.market_data.clients import DANE_POPULATION_LAYER, SOCRATA_BASE  # noqa: E402
from infrastructure.resilience.circuit_breaker import CircuitBreaker  # noqa: E402
from infrastructure.resilience.http_client import ResilientHttpClient, TransientHttpError  # noqa: E402
from infrastructure.resilience.retry import RetryPolicy  # noqa: E402

SHOW = 3


def client(host):
    return ResilientHttpClient(CircuitBreaker(host, failure_exceptions=(TransientHttpError,)),
                               RetryPolicy(max_retries=2, retry_on=(TransientHttpError,)))


def call(http, title, url, params, records_of=lambda data: data):
    started = time.perf_counter()
    data = http.get_json(url, params)
    elapsed = (time.perf_counter() - started) * 1000
    records = records_of(data)
    print(f'### {title}')
    print(f'GET {url}')
    for key, value in params.items():
        print(f'    {key} = {value}')
    print(f'-> HTTP 200 en {elapsed:.0f} ms | intentos: {http.last_stats.attempts} | breaker: {http.breaker.state.value}'
          f' | {len(records)} registros (se muestran {min(SHOW, len(records))})')
    print(json.dumps(records[:SHOW], ensure_ascii=False, indent=2))
    if len(records) > SHOW:
        print(f'... ({len(records) - SHOW} registros mas, omitidos en la captura)')
    print()


def main(target):
    print(f'Consulta real: {datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")}\n')
    if target == 'datos.gov.co':
        http = client('datos.gov.co')
        call(http, 'RUNT - Crecimiento del parque automotor (MinTransporte) u3vn-bdcy', f'{SOCRATA_BASE}/u3vn-bdcy.json', {
            '$select': 'nombre_departamento, nombre_de_la_clase, fecha_de_registro, sum(cantidad) as vehiculos',
            '$where': "estado_del_vehiculo = 'ACTIVO'",
            '$group': 'nombre_departamento, nombre_de_la_clase, fecha_de_registro',
            '$order': 'vehiculos DESC', '$limit': 50000})
        call(http, 'DIVIPOLA - Codigos de municipios (DANE) gdxc-w37w', f'{SOCRATA_BASE}/gdxc-w37w.json',
             {'$select': 'cod_dpto, dpto, cod_mpio, nom_mpio', '$order': 'cod_mpio', '$limit': 5000})
    elif target == 'dane':
        http = client('geoportal.dane.gov.co')
        call(http, 'DANE geoportal (ArcGIS REST) - Poblacion total censada CNPV 2018 por municipio',
             f'{DANE_POPULATION_LAYER}/query',
             {'where': '1=1', 'outFields': 'DPTO_CCDGO,MPIO_CCDGO,MPIO_CNMBR,CL0_TT_PERSN', 'returnGeometry': 'false',
              'orderByFields': 'CL0_TT_PERSN DESC', 'f': 'json'},
             records_of=lambda data: data['features'])
    else:
        sys.exit('uso: consultar_apis.py datos.gov.co|dane')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '')
