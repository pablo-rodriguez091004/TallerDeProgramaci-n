"""
Estimacion de costos del LLM a partir de los tokens REALES medidos en
evidence/prompt_eval/results.json (scripts/run_prompt_eval.py).

Formula (Gemini factura los tokens de "thinking" como salida):
  cost_per_call = avg_input_tokens  * input_price  / 1e6
                + (avg_output_tokens + avg_thinking_tokens) * output_price / 1e6
  monthly_cost  = cost_per_call * queries_per_day * days_per_month

Los precios y la fuente se pasan como parametros: si cambian, se vuelve a
correr con los valores nuevos (ver --help). Por defecto: precios de pago
(Standard tier) de gemini-3.5-flash-lite consultados el 2026-10-20.

Salidas (en ingles, requisito de la guia):
  evidence/cost_estimate.json
  evidence/cost_estimate_EN.md
"""

import argparse
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RESULTS = os.path.join(ROOT, 'evidence', 'prompt_eval', 'results.json')
OUT_JSON = os.path.join(ROOT, 'evidence', 'cost_estimate.json')
OUT_MD = os.path.join(ROOT, 'evidence', 'cost_estimate_EN.md')

PRICING_URL = 'https://ai.google.dev/gemini-api/docs/pricing'
PRICING_ACCESSED = '2026-10-20'
PRICING_PAGE_UPDATED = '2026-10-19'


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--input-price', type=float, default=0.30, help='USD per 1M input tokens (paid tier).')
    p.add_argument('--output-price', type=float, default=2.50,
                   help='USD per 1M output tokens, thinking included (paid tier).')
    p.add_argument('--queries-per-day', type=int, default=50)
    p.add_argument('--days', type=int, default=30)
    p.add_argument('--usd-to-cop', type=float, default=None,
                   help='Optional exchange rate to also show COP (not used unless given).')
    return p.parse_args()


def main():
    args = parse_args()
    with open(RESULTS, encoding='utf-8') as f:
        data = json.load(f)
    model = data['metadata']['model']
    calls = data['results']
    retried = sum(1 for r in calls if (r.get('attempts') or 1) > 1)
    monthly_calls = args.queries_per_day * args.days

    rows = {}
    for technique, s in data['summary'].items():
        billed_output = s['avg_output_tokens'] + (s['avg_thinking_tokens'] or 0)
        input_cost = s['avg_input_tokens'] * args.input_price / 1e6
        output_cost = billed_output * args.output_price / 1e6
        per_call = input_cost + output_cost
        rows[technique] = {
            'avg_input_tokens': s['avg_input_tokens'],
            'avg_output_tokens': s['avg_output_tokens'],
            'avg_thinking_tokens': s['avg_thinking_tokens'],
            'cost_per_call_usd': round(per_call, 8),
            'cost_per_1000_calls_usd': round(per_call * 1000, 4),
            'monthly_cost_usd': round(per_call * monthly_calls, 4),
            'precision_top1': s['precision_top1'],
        }

    output = {
        'model': model,
        'pricing': {'input_usd_per_1m': args.input_price, 'output_usd_per_1m': args.output_price,
                    'tier': 'Paid tier (Standard)', 'source_url': PRICING_URL,
                    'accessed': PRICING_ACCESSED, 'page_last_updated': PRICING_PAGE_UPDATED},
        'assumptions': {'queries_per_day': args.queries_per_day, 'days_per_month': args.days,
                        'monthly_calls': monthly_calls,
                        'token_source': 'averages of the real calls in evidence/prompt_eval/results.json',
                        'one_llm_call_per_query': True, 'retries_not_billed_extra': True},
        'by_technique': rows,
    }
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
        f.write('\n')

    fmt = lambda v: f'{v:,.6f}'  # noqa: E731
    lines = [
        '# LLM Cost Estimate - MecaTrack AI Assistant',
        '',
        f'**Model:** `{model}` (Google Gemini API). '
        f'**Price (paid tier, Standard):** ${args.input_price:.2f} per 1M input tokens and '
        f'${args.output_price:.2f} per 1M output tokens (thinking tokens are billed as output). '
        f'Source: Google AI for Developers, *Gemini Developer API pricing*, {PRICING_URL} '
        f'(page last updated {PRICING_PAGE_UPDATED}, accessed {PRICING_ACCESSED}).',
        '',
        '## Formula',
        '',
        '```',
        'cost_per_call = avg_input_tokens x input_price / 1,000,000',
        '              + (avg_output_tokens + avg_thinking_tokens) x output_price / 1,000,000',
        'monthly_cost  = cost_per_call x queries_per_day x days_per_month',
        '```',
        '',
        f'## Assumptions',
        '',
        f'- {args.queries_per_day} queries per day x {args.days} days = **{monthly_calls:,} calls per month**.',
        '- Average tokens are measured, not estimated: they come from the 30 real calls of the prompt '
        'experiment (10 cases x 3 techniques).',
        f'- One LLM call per customer query. Retries after a 429/503 happened in {retried} of {len(calls)} '
        'calls of the experiment; the failed attempt reported no token usage, so nothing is added for it.',
        '- The retrieval step (keyword matching) runs in our server and has no API cost.',
        '',
        '## Results',
        '',
        '| Technique | Avg input tokens | Avg output tokens | Cost per call (USD) | Cost per 1,000 calls (USD) '
        '| Monthly cost (USD) | Top-1 precision |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for technique, r in rows.items():
        lines.append(f"| {technique} | {r['avg_input_tokens']} | {r['avg_output_tokens']} | "
                     f"{fmt(r['cost_per_call_usd'])} | {r['cost_per_1000_calls_usd']:.4f} | "
                     f"{r['monthly_cost_usd']:.4f} | {r['precision_top1']:.0%} |")
    cheapest = min(rows, key=lambda t: rows[t]['cost_per_call_usd'])
    priciest = max(rows, key=lambda t: rows[t]['cost_per_call_usd'])
    ratio = rows[priciest]['cost_per_call_usd'] / rows[cheapest]['cost_per_call_usd']
    lines += [
        '',
        '## Reading the numbers',
        '',
        f'- Every technique costs **less than one US dollar per month** at this volume. '
        f'`{priciest}` is about {ratio:.1f}x more expensive per call than `{cheapest}`.',
        f"- Few-shot uses {rows['few_shot']['avg_input_tokens'] / rows['zero_shot']['avg_input_tokens']:.1f}x the "
        '**input** tokens of zero-shot (the three examples travel in every prompt); chain-of-thought uses '
        f"{rows['cot']['avg_output_tokens'] / rows['zero_shot']['avg_output_tokens']:.1f}x the **output** tokens "
        f'(the written reasoning), and output tokens cost {args.output_price / args.input_price:.1f}x more than '
        'input tokens with this model.',
        '- The free tier of this model costs $0, but it has stricter rate limits and Google states that '
        'free-tier content is *used to improve our products*; for real customer data the paid tier '
        '(not used for that purpose) is the safer choice.',
    ]
    if args.usd_to_cop:
        lines.append(f'- With 1 USD = {args.usd_to_cop:,.0f} COP, the most expensive option costs about '
                     f'{rows[priciest]["monthly_cost_usd"] * args.usd_to_cop:,.0f} COP per month.')
    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    print('\n'.join(lines))


if __name__ == '__main__':
    main()
