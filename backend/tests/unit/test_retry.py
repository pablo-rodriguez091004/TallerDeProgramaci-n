"""Retry con backoff exponencial y jitter: tiempos verificados con sleep y rng falsos."""

import pytest

from infrastructure.resilience.retry import RetryExhausted, RetryPolicy, RetryStats, retry_call


class Flaky:
    """Falla `failures` veces y luego responde."""

    def __init__(self, failures, error=ConnectionError):
        self.failures = failures
        self.error = error
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.calls <= self.failures:
            raise self.error(f'fallo {self.calls}')
        return 'ok'


@pytest.fixture
def slept():
    return []


def test_succeeds_after_transient_failures_waiting_exponentially(slept):
    policy = RetryPolicy(max_retries=3, base_delay=0.5, factor=2, max_delay=8, retry_on=(ConnectionError,))
    stats = RetryStats()

    # rng=1.0 -> espera = techo completo: 0.5, 1, 2 (crece x2)
    assert retry_call(Flaky(3), policy, sleep=slept.append, rng=lambda: 1.0, stats=stats) == 'ok'
    assert slept == [0.5, 1.0, 2.0]
    assert (stats.attempts, stats.delays) == (4, slept)


def test_equal_jitter_keeps_each_delay_between_half_and_full_ceiling(slept):
    policy = RetryPolicy(max_retries=3, base_delay=0.5, retry_on=(ConnectionError,))
    retry_call(Flaky(3), policy, sleep=slept.append, rng=lambda: 0.0)
    assert slept == [0.25, 0.5, 1.0]  # rng=0 -> la mitad del techo (minimo)

    for n in range(1, 8):
        ceiling = policy.ceiling(n)
        assert ceiling / 2 <= policy.delay(n) <= ceiling


def test_delay_is_capped_by_max_delay():
    policy = RetryPolicy(base_delay=1, factor=2, max_delay=8)
    assert [policy.ceiling(n) for n in range(1, 7)] == [1, 2, 4, 8, 8, 8]


def test_gives_up_after_max_retries_with_the_last_error(slept):
    flaky = Flaky(10)
    with pytest.raises(RetryExhausted) as error:
        retry_call(flaky, RetryPolicy(max_retries=2, retry_on=(ConnectionError,)), sleep=slept.append)
    assert flaky.calls == 3 and len(slept) == 2  # 1 intento + 2 reintentos
    assert error.value.attempts == 3 and str(error.value.last_error) == 'fallo 3'


def test_non_retryable_errors_propagate_immediately(slept):
    flaky = Flaky(1, error=ValueError)
    with pytest.raises(ValueError):
        retry_call(flaky, RetryPolicy(retry_on=(ConnectionError,)), sleep=slept.append)
    assert flaky.calls == 1 and slept == []
