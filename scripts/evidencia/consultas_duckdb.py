"""
Ejecuta las consultas analiticas de DuckDB sobre los snapshots descargados
y muestra el resultado con la tabla nativa de DuckDB (relation.show()).

    backend/venv/bin/python scripts/evidencia/consultas_duckdb.py q1|q2
"""

import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'backend'))

import duckdb  # noqa: E402

from config import Config  # noqa: E402
from infrastructure.analytics import queries  # noqa: E402
from infrastructure.analytics.duckdb_analytics import DuckDbMarketAnalytics  # noqa: E402

QUERIES = {
    'q1': ('Q1 - Antiguedad del parque por clase (estadisticas ponderadas)', ['runt'],
           [queries.FLEET_AGE_BY_CLASS]),
    'q2': ('Q2 - Motorizacion por departamento + resumen entre departamentos', ['runt', 'divipola', 'poblacion'],
           [queries.MOTORIZATION_BY_DEPARTMENT, queries.MOTORIZATION_SUMMARY]),
}


def main(key):
    title, views, sqls = QUERIES[key]
    analytics = DuckDbMarketAnalytics(Config.MARKET_DATA_DIR)
    con, snapshots = analytics._connect(views)
    print(f'DuckDB {duckdb.__version__} | snapshots: ' + ', '.join(f'{k} {v}' for k, v in snapshots.items()))
    print(title)
    for i, sql in enumerate(sqls):
        started = time.perf_counter()
        if i == 0 and key == 'q2':
            con.execute(f'CREATE TEMP TABLE motorizacion AS {sql}')
            relation = con.sql('SELECT puesto, departamento, poblacion_2018, vehiculos, vehiculos_por_1000_hab, '
                               'pct_motos FROM motorizacion ORDER BY puesto')
        else:
            relation = con.sql(sql)
        rows = relation.fetchall()
        elapsed = (time.perf_counter() - started) * 1000
        relation.show(max_width=200, max_rows=40)
        print(f'{len(rows)} filas en {elapsed:.1f} ms\n')
    con.close()


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'q1')
