"""
Exporta los resultados REALES de las 3 consultas DuckDB (mismo adaptador que
usa la API) a docs/evidencia/salidas/analitica.json para el informe Word.
"""

import json
import os
import sys
from dataclasses import asdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'backend'))

from config import Config  # noqa: E402
from infrastructure.analytics.duckdb_analytics import DuckDbMarketAnalytics  # noqa: E402

analytics = DuckDbMarketAnalytics(Config.MARKET_DATA_DIR)
result = {name: asdict(getattr(analytics, name)())
          for name in ('fleet_age_by_class', 'motorization_by_department', 'age_distribution')}
out = os.path.join(ROOT, 'docs', 'evidencia', 'salidas', 'analitica.json')
with open(out, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print(f'{out}: ' + ', '.join(f'{k} {len(v["rows"])} filas ({v["elapsed_ms"]} ms)' for k, v in result.items()))
