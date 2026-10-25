"""
DEMOSTRACION CONTROLADA de resiliencia con llamadas de red REALES.

Usa los mismos componentes que la app (CircuitBreaker, RetryPolicy,
ResilientHttpClient). Los fallos se fuerzan de forma controlada con un host
del dominio reservado .invalid (RFC 2606: nunca resuelve), asi el error de
DNS es real; las llamadas exitosas van a datos.gov.co de verdad.

Parte A - Retry con backoff exponencial + jitter: tiempos reales entre intentos.
Parte B - Circuit breaker: CLOSED -> OPEN -> HALF_OPEN -> OPEN -> HALF_OPEN -> CLOSED.

Uso:
    backend/venv/bin/python scripts/demo_resilience.py [--json salida.json]
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'backend'))

from infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitOpenError  # noqa: E402
from infrastructure.resilience.http_client import ResilientHttpClient, TransientHttpError  # noqa: E402
from infrastructure.resilience.retry import RetryExhausted, RetryPolicy  # noqa: E402

GOOD_URL = 'https://www.datos.gov.co/resource/gdxc-w37w.json'   # DIVIPOLA (DANE)
GOOD_PARAMS = {'$limit': 1, '$select': 'cod_mpio, nom_mpio'}
BAD_URL = 'https://datos-gov-co.invalid/resource/gdxc-w37w.json'  # fallo controlado
RECOVERY_S = 5

STARTED = time.perf_counter()
events = []


def stamp():
    return datetime.now(timezone.utc).astimezone().strftime('%H:%M:%S.%f')[:-3]


def log(kind, message, **data):
    elapsed = time.perf_counter() - STARTED
    print(f'[{stamp()}] +{elapsed:7.3f}s  {kind:<11} {message}', flush=True)
    events.append({'t': round(elapsed, 3), 'kind': kind, 'message': message, **data})


class TransitionPrinter(logging.Handler):
    """Imprime cada transicion del breaker en el momento en que ocurre."""

    def emit(self, record):
        message = record.getMessage()
        if message.startswith('circuit '):
            log('TRANSITION', message)


def part_a():
    print('\n=== Parte A: retry con backoff exponencial + jitter (equal jitter) ===')
    policy = RetryPolicy(max_retries=4, base_delay=0.5, factor=2, max_delay=8, retry_on=(TransientHttpError,))
    print(f'Politica: {policy.max_retries} reintentos, techo = min({policy.max_delay:g}, '
          f'{policy.base_delay:g} * {policy.factor:g}^(n-1)), espera = techo/2 + U(0, techo/2)')
    breaker = CircuitBreaker('retry-demo', failure_threshold=99, failure_exceptions=(TransientHttpError,))
    attempts = []

    def sleep(seconds):
        log('BACKOFF', f'espera planificada {seconds:.3f} s (techo {policy.ceiling(len(attempts)):g} s)',
            planned_s=round(seconds, 3))
        time.sleep(seconds)

    client = ResilientHttpClient(breaker, policy, timeout_s=10, sleep=sleep)
    original = client._request

    def traced(url, params):
        attempts.append(time.perf_counter())
        gap = '' if len(attempts) == 1 else f' (+{attempts[-1] - attempts[-2]:.3f} s desde el anterior)'
        log('ATTEMPT', f'intento {len(attempts)} -> {url}{gap}')
        return original(url, params)

    client._request = traced
    try:
        client.get_json(BAD_URL, GOOD_PARAMS)
    except RetryExhausted as exc:
        log('GAVE_UP', f'{exc.attempts} intentos: {exc.last_error}')
    gaps = [round(b - a, 3) for a, b in zip(attempts, attempts[1:])]
    print(f'Separacion real entre intentos (s): {gaps}')
    return {'gaps_s': gaps, 'planned_s': [round(d, 3) for d in client.last_stats.delays]}


def call(client, url, label):
    t0 = time.perf_counter()
    try:
        data = client.get_json(url, GOOD_PARAMS)
        log('OK', f'{label}: {data} en {(time.perf_counter() - t0) * 1000:.0f} ms | estado={client.breaker.state.value}')
    except CircuitOpenError as exc:
        log('REJECTED', f'{label}: {exc} (sin salir a la red, {(time.perf_counter() - t0) * 1e6:.0f} us)')
    except RetryExhausted as exc:
        log('FAILED', f'{label}: {exc.last_error} | estado={client.breaker.state.value} '
                      f'fallos={client.breaker.consecutive_failures}')


def part_b():
    print(f'\n=== Parte B: circuit breaker (umbral 3 fallos, recuperacion {RECOVERY_S} s) ===')
    breaker = CircuitBreaker('datos.gov.co', failure_threshold=3, recovery_timeout=RECOVERY_S,
                             failure_exceptions=(TransientHttpError,))
    # Sin reintentos aqui: cada llamada es un solo intento y se ve cada fallo.
    client = ResilientHttpClient(breaker, RetryPolicy(max_retries=0, retry_on=(TransientHttpError,)), timeout_s=10)
    log('STATE', f'estado inicial: {breaker.state.value}')

    call(client, GOOD_URL, '1. llamada real a datos.gov.co')
    for i in (2, 3, 4):
        call(client, BAD_URL, f'{i}. fallo controlado (host .invalid)')
    call(client, GOOD_URL, '5. llamada con el circuito abierto')

    log('WAIT', f'esperando {RECOVERY_S} s de recuperacion...')
    time.sleep(RECOVERY_S)
    log('STATE', f'tras la espera: {breaker.state.value}')
    call(client, BAD_URL, '6. prueba HALF_OPEN que falla')
    call(client, GOOD_URL, '7. llamada con el circuito re-abierto')

    log('WAIT', f'esperando {RECOVERY_S} s de recuperacion...')
    time.sleep(RECOVERY_S)
    log('STATE', f'tras la espera: {breaker.state.value}')
    call(client, GOOD_URL, '8. prueba HALF_OPEN real a datos.gov.co')
    log('STATE', f'estado final: {breaker.state.value}')
    return list(breaker.transitions)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--json', help='guarda los eventos en este archivo JSON')
    args = parser.parse_args()

    handler = TransitionPrinter()
    resilience_logger = logging.getLogger('mecatrack.resilience')
    resilience_logger.addHandler(handler)
    resilience_logger.setLevel(logging.WARNING)
    resilience_logger.propagate = False

    print('DEMOSTRACION CONTROLADA: fallos forzados con un host .invalid (RFC 2606); exitos contra datos.gov.co real.')
    print(f'Inicio: {datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")}')
    retry = part_a()
    transitions = part_b()
    print('\nTransiciones registradas por el breaker:')
    for t in transitions:
        print(f"  {t['from']:>9} -> {t['to']:<9} {t['reason']}")

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump({'retry': retry, 'transitions': transitions, 'events': events}, f, ensure_ascii=False, indent=1)
        print(f'\nEventos guardados en {os.path.relpath(args.json, ROOT)}')


if __name__ == '__main__':
    main()
