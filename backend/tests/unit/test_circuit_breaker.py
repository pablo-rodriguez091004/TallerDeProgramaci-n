"""
Transiciones del circuit breaker con un reloj falso (sin esperas reales):

    CLOSED -> OPEN -> HALF_OPEN -> CLOSED      (la dependencia se recupera)
    CLOSED -> OPEN -> HALF_OPEN -> OPEN        (sigue caida: el temporizador se reinicia)
"""

import pytest

from infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class Boom(Exception):
    pass


def fail():
    raise Boom('upstream 503')


def ok():
    return 'datos'


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def breaker(clock):
    return CircuitBreaker('datos.gov.co', failure_threshold=3, recovery_timeout=30, failure_exceptions=(Boom,),
                          clock=clock)


def trip(breaker):
    for _ in range(breaker.failure_threshold):
        with pytest.raises(Boom):
            breaker.call(fail)


def test_full_cycle_closed_open_half_open_closed(breaker, clock):
    assert breaker.state is CircuitState.CLOSED

    # 1) CLOSED: los fallos pasan y se cuentan; al tercero se abre
    for expected_failures in (1, 2):
        with pytest.raises(Boom):
            breaker.call(fail)
        assert (breaker.state, breaker.consecutive_failures) == (CircuitState.CLOSED, expected_failures)
    with pytest.raises(Boom):
        breaker.call(fail)
    assert breaker.state is CircuitState.OPEN

    # 2) OPEN: se rechaza SIN llamar a la funcion (fail fast)
    calls = []
    with pytest.raises(CircuitOpenError) as error:
        breaker.call(lambda: calls.append('no deberia ejecutarse'))
    assert calls == [] and error.value.retry_in_s == 30
    clock.advance(29.9)
    assert breaker.state is CircuitState.OPEN and breaker.retry_in() == pytest.approx(0.1)

    # 3) Vence el recovery timeout -> HALF_OPEN
    clock.advance(0.1)
    assert breaker.state is CircuitState.HALF_OPEN

    # 4) La llamada de prueba funciona -> CLOSED y el conteo se reinicia
    assert breaker.call(ok) == 'datos'
    assert (breaker.state, breaker.consecutive_failures) == (CircuitState.CLOSED, 0)

    assert [(t['from'], t['to']) for t in breaker.transitions] == [
        ('CLOSED', 'OPEN'), ('OPEN', 'HALF_OPEN'), ('HALF_OPEN', 'CLOSED')]
    assert '3 consecutive failures' in breaker.transitions[0]['reason']


def test_failed_trial_reopens_and_restarts_the_timer(breaker, clock):
    trip(breaker)
    clock.advance(30)
    assert breaker.state is CircuitState.HALF_OPEN

    with pytest.raises(Boom):
        breaker.call(fail)
    assert breaker.state is CircuitState.OPEN
    assert breaker.retry_in() == 30  # temporizador nuevo, no el viejo
    assert breaker.transitions[-1]['reason'].startswith('trial call failed')


def test_half_open_lets_only_one_trial_through(breaker, clock):
    trip(breaker)
    clock.advance(30)

    def trial():
        # Mientras la prueba esta en curso, otra llamada concurrente se rechaza.
        with pytest.raises(CircuitOpenError):
            breaker.call(ok)
        return 'prueba'

    assert breaker.call(trial) == 'prueba'
    assert breaker.state is CircuitState.CLOSED


def test_a_success_resets_the_consecutive_failure_count(breaker):
    for _ in range(2):
        with pytest.raises(Boom):
            breaker.call(fail)
    breaker.call(ok)
    for _ in range(2):
        with pytest.raises(Boom):
            breaker.call(fail)
    assert breaker.state is CircuitState.CLOSED  # 2 + 2 no son 3 seguidos


def test_errors_outside_failure_exceptions_do_not_open_the_circuit(breaker):
    for _ in range(5):
        with pytest.raises(KeyError):
            breaker.call(lambda: {}['x'])
    assert (breaker.state, breaker.consecutive_failures) == (CircuitState.CLOSED, 0)


def test_reset_closes_manually(breaker):
    trip(breaker)
    breaker.reset()
    assert breaker.state is CircuitState.CLOSED and breaker.call(ok) == 'datos'


def test_invalid_threshold():
    with pytest.raises(ValueError):
        CircuitBreaker('x', failure_threshold=0)
