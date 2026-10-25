"""
ResilientHttpClient con httpx.MockTransport: se ejecuta el cliente httpx
real (parametros, codigos HTTP, JSON) pero las respuestas son simuladas.
"""

import httpx
import pytest

from infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState
from infrastructure.resilience.http_client import (PermanentHttpError, ResilientHttpClient, RetryExhausted,
                                                   TransientHttpError)
from infrastructure.resilience.retry import RetryPolicy

URL = 'https://www.datos.gov.co/resource/u3vn-bdcy.json'


class Script:
    """Transporte que responde en orden lo indicado (status o excepcion)."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        outcome = self.outcomes.pop(0) if len(self.outcomes) > 1 else self.outcomes[0]
        if isinstance(outcome, Exception):
            raise outcome
        status, body = outcome
        return httpx.Response(status, json=body)


def make_client(script, threshold=3, retries=2):
    breaker = CircuitBreaker('datos.gov.co', failure_threshold=threshold, recovery_timeout=30,
                             failure_exceptions=(TransientHttpError,))
    policy = RetryPolicy(max_retries=retries, base_delay=0.5, retry_on=(TransientHttpError,))
    slept = []
    client = ResilientHttpClient(breaker, policy, transport=httpx.MockTransport(script), sleep=slept.append)
    return client, breaker, slept


def test_retries_5xx_and_timeouts_then_returns_json():
    script = Script((503, {}), httpx.ReadTimeout('lento'), (200, [{'cantidad': '1'}]))
    client, breaker, slept = make_client(script)

    assert client.get_json(URL, {'$limit': 1}) == [{'cantidad': '1'}]
    assert len(script.requests) == 3 and len(slept) == 2
    assert script.requests[0].url.params['$limit'] == '1'
    assert client.last_stats.attempts == 3
    assert breaker.state is CircuitState.CLOSED  # el exito reinicio el conteo


def test_4xx_is_permanent_no_retry_and_does_not_open_the_circuit():
    script = Script((400, {'message': 'bad SoQL'}))
    client, breaker, slept = make_client(script, threshold=1)
    with pytest.raises(PermanentHttpError) as error:
        client.get_json(URL)
    assert error.value.status_code == 400 and len(script.requests) == 1 and slept == []
    assert breaker.state is CircuitState.CLOSED


def test_circuit_opens_mid_retries_and_then_fails_fast_without_network():
    script = Script(httpx.ConnectError('sin red'))
    client, breaker, slept = make_client(script, threshold=3, retries=5)

    # 3 fallos reales abren el circuito; el 4o intento ya no sale a la red
    with pytest.raises(CircuitOpenError):
        client.get_json(URL)
    assert len(script.requests) == 3 and breaker.state is CircuitState.OPEN

    with pytest.raises(CircuitOpenError):
        client.get_json(URL)
    assert len(script.requests) == 3  # fail fast: ninguna peticion nueva


def test_retry_exhausted_when_failures_stay_below_the_threshold():
    script = Script((502, {}))
    client, breaker, _ = make_client(script, threshold=10, retries=2)
    with pytest.raises(RetryExhausted):
        client.get_json(URL)
    assert len(script.requests) == 3 and breaker.consecutive_failures == 3
