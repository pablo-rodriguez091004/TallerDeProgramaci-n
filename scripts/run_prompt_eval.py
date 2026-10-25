"""
Experimento de tecnicas de prompting (Guia 5, fase 5).

Ejecuta los casos de evidence/prompt_eval/cases.json con las 3 tecnicas
(zero_shot, few_shot, cot) llamando al LLM REAL a traves del mismo servicio
que usa el endpoint (application/ai_assistant/services.py). Cada llamada queda ademas en la
tabla ai_calls con source='eval'.

Salidas:
  evidence/prompt_eval/results.json  detalle por llamada + resumen por tecnica
  evidence/prompt_eval/results.csv   una fila por llamada

Metricas por tecnica:
  precision_top1   aciertos / casos (acierto = el servicio esperado es la 1a sugerencia)
  hit_rate_top3    el servicio esperado aparece entre las sugerencias
  retrieval_recall el servicio esperado estaba en el contexto RAG (si no, el LLM no podia acertar)
  tokens promedio de entrada / salida / thinking y latencia promedio (solo llamadas exitosas)

Uso:
  backend/venv/bin/python scripts/run_prompt_eval.py [--delay 5] [--techniques zero_shot,few_shot,cot]

Requiere GEMINI_API_KEY y GEMINI_MODEL en backend/.env y el catalogo de
database/catalog.sql cargado (./scripts/seed_catalog.sh).
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from statistics import mean

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'backend'))
EVAL_DIR = os.path.join(ROOT, 'evidence', 'prompt_eval')

from app import create_app  # noqa: E402
from domain.ai_assistant import prompts  # noqa: E402
from domain.ai_assistant.errors import InvalidModelResponse, LlmError  # noqa: E402
from infrastructure.persistence.extensions import db  # noqa: E402
from infrastructure.persistence.models import AiCall  # noqa: E402


def run_case(assistant, case, technique):
    row = {'case_id': case['id'], 'technique': technique, 'description': case['description'],
           'expected_service_id': case['expected_service_id']}
    try:
        result = assistant.suggest_services(case['description'], technique, source='eval')
    except (LlmError, InvalidModelResponse) as exc:
        call = db.session.get(AiCall, getattr(exc, 'ai_call_id', None)) if getattr(exc, 'ai_call_id', None) else None
        row.update(status=call.status if call else 'error', error=str(exc), ai_call_id=getattr(exc, 'ai_call_id', None),
                   suggested_service_ids=[], hit_top1=False, hit_top3=False, retrieval_hit=None,
                   input_tokens=call.input_tokens if call else None,
                   output_tokens=call.output_tokens if call else None,
                   thinking_tokens=call.thinking_tokens if call else None,
                   latency_ms=call.latency_ms if call else None, attempts=getattr(exc, 'attempts', None),
                   prompt=call.prompt if call else None, response=call.response if call else None)
        return row

    call = db.session.get(AiCall, result['ai_call_id'])
    suggested = [s['service_id'] for s in result['suggestions']]
    expected = case['expected_service_id']
    row.update(
        status='success', error=None, ai_call_id=result['ai_call_id'], model=result['model'],
        suggested_service_ids=suggested,
        suggestions=result['suggestions'],
        hit_top1=bool(suggested) and suggested[0] == expected,
        hit_top3=expected in suggested,
        retrieval_hit=expected in result['retrieval']['candidate_service_ids'],
        retrieval_candidates=result['retrieval']['candidate_service_ids'],
        retrieval_fallback=result['retrieval']['fallback_full_catalog'],
        discarded_service_ids=result['discarded_service_ids'],
        notes=result['notes'], reasoning=result['reasoning'],
        input_tokens=result['usage']['input_tokens'], output_tokens=result['usage']['output_tokens'],
        thinking_tokens=result['usage']['thinking_tokens'], latency_ms=result['usage']['latency_ms'],
        attempts=result['usage']['attempts'],
        prompt=call.prompt, response=call.response,
    )
    return row


def summarize(rows, techniques, total_cases):
    summary = {}
    for technique in techniques:
        mine = [r for r in rows if r['technique'] == technique]
        ok = [r for r in mine if r['status'] == 'success']

        def avg(key):
            values = [r[key] for r in ok if r[key] is not None]
            return round(mean(values), 1) if values else None

        summary[technique] = {
            'calls': len(mine),
            'successful_calls': len(ok),
            'hits_top1': sum(r['hit_top1'] for r in mine),
            'precision_top1': round(sum(r['hit_top1'] for r in mine) / total_cases, 2),
            'hit_rate_top3': round(sum(r['hit_top3'] for r in mine) / total_cases, 2),
            'retrieval_recall': round(sum(bool(r['retrieval_hit']) for r in mine) / total_cases, 2),
            'hallucinated_ids_discarded': sum(len(r.get('discarded_service_ids') or []) for r in mine),
            'avg_input_tokens': avg('input_tokens'),
            'avg_output_tokens': avg('output_tokens'),
            'avg_thinking_tokens': avg('thinking_tokens'),
            'avg_latency_ms': avg('latency_ms'),
            'max_latency_ms': max((r['latency_ms'] for r in ok), default=None),
        }
    return summary


CSV_FIELDS = ['case_id', 'technique', 'status', 'expected_service_id', 'suggested_service_ids', 'hit_top1',
              'hit_top3', 'retrieval_hit', 'input_tokens', 'output_tokens', 'thinking_tokens', 'latency_ms',
              'attempts', 'ai_call_id', 'description', 'notes', 'reasoning', 'error', 'response', 'prompt']


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--delay', type=float, default=5.0,
                        help='Segundos entre llamadas (cuida el limite por minuto de la capa gratuita).')
    parser.add_argument('--techniques', default=','.join(prompts.TECHNIQUES))
    args = parser.parse_args()
    techniques = args.techniques.split(',')

    with open(os.path.join(EVAL_DIR, 'cases.json'), encoding='utf-8') as f:
        cases = json.load(f)

    app = create_app()
    rows = []
    started_at = datetime.now(timezone.utc)
    with app.app_context():
        if not app.config.get('GEMINI_API_KEY') or not app.config.get('GEMINI_MODEL'):
            sys.exit('Falta GEMINI_API_KEY o GEMINI_MODEL en backend/.env: no se ejecuta nada.')
        assistant = app.extensions['mecatrack'].ai_assistant
        # Sin terminos de busqueda, retrieve() cae al catalogo activo completo.
        catalog = [{'service_id': s.service_id, 'service_name': s.service_name}
                   for s in assistant.retrieve('')['services']]
        missing = {c['expected_service_id'] for c in cases} - {s['service_id'] for s in catalog}
        if missing:
            sys.exit(f'El catalogo activo no tiene los servicios esperados {missing}: corre ./scripts/seed_catalog.sh')

        total = len(cases) * len(techniques)
        # Caso por caso alternando tecnicas: una degradacion temporal del
        # proveedor afecta a las tres por igual, no a una sola.
        for case in cases:
            for technique in techniques:
                if rows:
                    time.sleep(args.delay)
                row = run_case(assistant, case, technique)
                rows.append(row)
                mark = 'OK ' if row['hit_top1'] else ('top3' if row['hit_top3'] else 'X  ')
                print(f"[{len(rows):2}/{total}] caso {case['id']:2} {technique:9} {row['status']:16} {mark} "
                      f"esperado={case['expected_service_id']:2} sugeridos={row['suggested_service_ids']} "
                      f"in={row['input_tokens']} out={row['output_tokens']} {row['latency_ms']} ms", flush=True)
        model = app.config['GEMINI_MODEL']

    summary = summarize(rows, techniques, len(cases))
    output = {
        'metadata': {
            'started_at_utc': started_at.isoformat(timespec='seconds'),
            'finished_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'provider': 'Google Gemini API (google-genai SDK)',
            'model': model,
            'temperature': 0.2,
            'cases': len(cases),
            'techniques': techniques,
            'delay_between_calls_s': args.delay,
            'metric_definitions': {
                'precision_top1': 'cases where the expected service is the first suggestion / total cases',
                'hit_rate_top3': 'cases where the expected service is among the suggestions / total cases',
                'retrieval_recall': 'cases where the expected service was in the RAG context / total cases',
                'latency_ms': 'end-to-end time of the provider call, retries included',
            },
            'catalog': catalog,
        },
        'summary': summary,
        'results': rows,
    }
    with open(os.path.join(EVAL_DIR, 'results.json'), 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write('\n')
    with open(os.path.join(EVAL_DIR, 'results.csv'), 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, 'suggested_service_ids': ' '.join(map(str, row['suggested_service_ids']))})

    print('\nResumen por tecnica:')
    print(json.dumps(summary, indent=2))
    print(f'\nGuardado en {os.path.relpath(EVAL_DIR, ROOT)}/results.json y results.csv')


if __name__ == '__main__':
    main()
