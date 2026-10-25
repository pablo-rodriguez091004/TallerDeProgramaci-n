"""
Exporta la tabla ai_calls de la base de desarrollo a evidence/ai_calls_export.{json,csv}
(evidencia de las llamadas reales al LLM). No incluye el prompt completo
(esta en results.json para las llamadas de la evaluacion) para que sea legible.

Uso: backend/venv/bin/python scripts/export_ai_calls.py
"""

import csv
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'backend'))

from app import create_app  # noqa: E402
from infrastructure.persistence.models import AiCall  # noqa: E402

FIELDS = ['ai_call_id', 'created_at', 'source', 'user_id', 'technique', 'model', 'status', 'input_tokens',
          'output_tokens', 'thinking_tokens', 'latency_ms', 'attempts', 'description', 'response', 'error_message']


def main():
    app = create_app()
    with app.app_context():
        rows = [{f: getattr(c, f) for f in FIELDS} for c in AiCall.query.order_by(AiCall.ai_call_id)]
    for row in rows:
        row['created_at'] = row['created_at'].isoformat(sep=' ', timespec='seconds')

    out = os.path.join(ROOT, 'evidence', 'ai_calls_export')
    with open(out + '.json', 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
        f.write('\n')
    with open(out + '.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    by_status = {}
    for row in rows:
        by_status[row['status']] = by_status.get(row['status'], 0) + 1
    print(f'{len(rows)} llamadas exportadas a evidence/ai_calls_export.json/.csv; por estado: {by_status}')


if __name__ == '__main__':
    main()
