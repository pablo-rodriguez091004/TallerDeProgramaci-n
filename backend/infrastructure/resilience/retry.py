"""
Reintentos con backoff exponencial y jitter.

Espera antes del reintento n (n = 1, 2, ...):

    techo_n = min(max_delay, base_delay * factor ** (n - 1))     # exponencial: 0.5, 1, 2, 4, ...
    espera  = techo_n / 2 + uniforme(0, techo_n / 2)               # "equal jitter"

El jitter reparte los reintentos de muchos clientes en el tiempo y evita
que todos golpeen a la vez a una API que se esta recuperando (Brooker,
"Exponential Backoff And Jitter", AWS Architecture Blog, 2015). Se usa
"equal jitter" (y no "full jitter") para que siempre haya una espera minima
creciente, visible en la evidencia.

Solo se reintentan las excepciones de `retry_on` (errores transitorios:
timeouts, conexion, HTTP 429/5xx). `sleep` y `rng` se inyectan para probar
los tiempos sin esperar de verdad.
"""

import logging
import random
import time
from dataclasses import dataclass, field

logger = logging.getLogger('mecatrack.resilience')


@dataclass
class RetryPolicy:
    max_retries: int = 3          # reintentos ADEMAS del primer intento
    base_delay: float = 0.5
    factor: float = 2.0
    max_delay: float = 8.0
    retry_on: tuple = (Exception,)

    def ceiling(self, retry_number):
        return min(self.max_delay, self.base_delay * self.factor ** (retry_number - 1))

    def delay(self, retry_number, rng=random.random):
        ceiling = self.ceiling(retry_number)
        return ceiling / 2 + rng() * ceiling / 2


@dataclass
class RetryStats:
    """Lo que paso en la ultima ejecucion (para logs y evidencia)."""
    attempts: int = 0
    delays: list = field(default_factory=list)


class RetryExhausted(Exception):
    def __init__(self, attempts, last_error):
        super().__init__(f'Gave up after {attempts} attempts: {type(last_error).__name__}: {last_error}')
        self.attempts = attempts
        self.last_error = last_error


def retry_call(fn, policy=None, sleep=time.sleep, rng=random.random, stats=None, label='call'):
    """
    Ejecuta fn(); si lanza una excepcion de policy.retry_on, espera y repite.
    Al agotar los reintentos lanza RetryExhausted (con el ultimo error).
    Las excepciones que no estan en retry_on se propagan de inmediato.
    """
    policy = policy or RetryPolicy()
    stats = stats if stats is not None else RetryStats()
    attempt = 0
    while True:
        attempt += 1
        stats.attempts = attempt
        try:
            return fn()
        except policy.retry_on as exc:
            if attempt > policy.max_retries:
                raise RetryExhausted(attempt, exc) from exc
            delay = policy.delay(attempt, rng)
            stats.delays.append(delay)
            logger.warning('%s failed (attempt %d/%d: %s: %s); retrying in %.3f s',
                           label, attempt, policy.max_retries + 1, type(exc).__name__, exc, delay)
            sleep(delay)
