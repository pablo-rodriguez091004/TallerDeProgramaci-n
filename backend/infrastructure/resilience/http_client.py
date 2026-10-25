"""
Cliente HTTP JSON resiliente: httpx + retry con backoff + circuit breaker.

    get_json() ── retry_call ──> breaker.call ──> httpx GET
                  (externo)        (interno)

- Cada intento pasa por el breaker, asi cada fallo real cuenta para abrirlo.
- CircuitOpenError NO se reintenta: si el circuito se abre a mitad de los
  reintentos, se deja de insistir de inmediato (fail fast).
- Transitorio (se reintenta y cuenta para el breaker): timeout, error de
  conexion, HTTP 429 y 5xx.
- Permanente (ni se reintenta ni abre el circuito): otros 4xx (la peticion
  esta mal, la dependencia esta sana).
"""

import time

import httpx

from infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitOpenError
from infrastructure.resilience.retry import RetryExhausted, RetryPolicy, RetryStats, retry_call

USER_AGENT = 'MecaTrack/1.0 (proyecto academico UMB)'


class TransientHttpError(Exception):
    """La dependencia fallo de forma temporal: vale la pena reintentar."""


class PermanentHttpError(Exception):
    def __init__(self, status_code, url):
        super().__init__(f'HTTP {status_code} for {url}')
        self.status_code = status_code


class ResilientHttpClient:

    def __init__(self, breaker: CircuitBreaker, policy: RetryPolicy, timeout_s=20.0, transport=None,
                 sleep=time.sleep):
        self.breaker = breaker
        self.policy = policy
        self._sleep = sleep
        # transport se inyecta en las pruebas (httpx.MockTransport): sin red.
        self._http = httpx.Client(timeout=timeout_s, transport=transport, follow_redirects=True,
                                  headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
        self.last_stats = RetryStats()

    def _request(self, url, params):
        try:
            response = self._http.get(url, params=params)
        except httpx.TimeoutException as exc:
            raise TransientHttpError(f'timeout calling {url}') from exc
        except httpx.TransportError as exc:
            raise TransientHttpError(f'{type(exc).__name__} calling {url}') from exc
        if response.status_code == 429 or response.status_code >= 500:
            raise TransientHttpError(f'HTTP {response.status_code} from {url}')
        if response.status_code >= 400:
            raise PermanentHttpError(response.status_code, url)
        try:
            return response.json()
        except ValueError as exc:
            raise TransientHttpError(f'invalid JSON from {url}') from exc

    def get_json(self, url, params=None):
        """
        Devuelve el JSON decodificado. Lanza CircuitOpenError, RetryExhausted
        (con el ultimo TransientHttpError) o PermanentHttpError.
        """
        self.last_stats = RetryStats()
        return retry_call(lambda: self.breaker.call(self._request, url, params),
                          policy=self.policy, sleep=self._sleep, stats=self.last_stats,
                          label=f'GET {httpx.URL(url).host}')


# Reexportados para que los adaptadores no importen tres modulos.
__all__ = ['ResilientHttpClient', 'TransientHttpError', 'PermanentHttpError', 'CircuitOpenError', 'RetryExhausted']
