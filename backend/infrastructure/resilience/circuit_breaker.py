"""
Circuit breaker de 3 estados (Nygard, *Release It!*; Fowler, "CircuitBreaker").

    CLOSED ──(failure_threshold fallos seguidos)──> OPEN
    OPEN ──(pasan recovery_timeout segundos)──> HALF_OPEN
    HALF_OPEN ──(la llamada de prueba funciona)──> CLOSED
    HALF_OPEN ──(la llamada de prueba falla)──> OPEN (el temporizador se reinicia)

- CLOSED: las llamadas pasan; cada fallo suma y un exito reinicia el conteo.
- OPEN: las llamadas se rechazan al instante con CircuitOpenError, sin tocar
  la red: la dependencia caida no se martilla y el usuario no espera timeouts.
- HALF_OPEN: se deja pasar UNA llamada de prueba; las demas se rechazan
  mientras esa prueba esta en curso.

Solo cuentan como fallo las excepciones de `failure_exceptions` (por
ejemplo, timeouts o HTTP 5xx). Un 404 por un parametro mal escrito no dice
nada de la salud de la dependencia y no abre el circuito.

El reloj se inyecta (por defecto time.monotonic) para probar las
transiciones sin esperar de verdad. Es seguro entre hilos (un Lock).
"""

import logging
import threading
import time
from collections import deque
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger('mecatrack.resilience')


class CircuitState(str, Enum):
    CLOSED = 'CLOSED'
    OPEN = 'OPEN'
    HALF_OPEN = 'HALF_OPEN'


class CircuitOpenError(Exception):
    def __init__(self, name, retry_in_s):
        super().__init__(f"Circuit '{name}' is OPEN; next trial in {retry_in_s:.1f} s")
        self.name = name
        self.retry_in_s = retry_in_s


class CircuitBreaker:

    def __init__(self, name, failure_threshold=3, recovery_timeout=30.0, failure_exceptions=(Exception,),
                 clock=time.monotonic, history_size=20):
        if failure_threshold < 1:
            raise ValueError('failure_threshold must be >= 1')
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_exceptions = failure_exceptions
        self._clock = clock
        self._lock = threading.Lock()
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._opened_at = None
        self._trial_in_progress = False
        self.transitions = deque(maxlen=history_size)

    # --- consulta ---------------------------------------------------------------

    @property
    def state(self):
        with self._lock:
            self._refresh()
            return self._state

    @property
    def consecutive_failures(self):
        return self._failures

    def retry_in(self):
        """Segundos que faltan para la siguiente llamada de prueba (solo en OPEN)."""
        with self._lock:
            self._refresh()
            return self._remaining() if self._state is CircuitState.OPEN else None

    # --- uso ----------------------------------------------------------------------

    def call(self, fn, *args, **kwargs):
        self._before_call()
        try:
            result = fn(*args, **kwargs)
        except self.failure_exceptions as exc:
            self._on_failure(exc)
            raise
        except BaseException:
            # Un error que no cuenta como fallo igual libera la prueba HALF_OPEN.
            with self._lock:
                self._trial_in_progress = False
            raise
        self._on_success()
        return result

    def reset(self):
        with self._lock:
            self._transition(CircuitState.CLOSED, 'manual reset')
            self._failures = 0

    # --- internos (siempre con el lock tomado) ---------------------------------------

    def _remaining(self):
        return max(0.0, self.recovery_timeout - (self._clock() - self._opened_at))

    def _refresh(self):
        """OPEN pasa a HALF_OPEN cuando vence el tiempo de recuperacion."""
        if self._state is CircuitState.OPEN and self._remaining() == 0:
            self._transition(CircuitState.HALF_OPEN, f'recovery timeout of {self.recovery_timeout:g} s elapsed')

    def _before_call(self):
        with self._lock:
            self._refresh()
            if self._state is CircuitState.OPEN:
                raise CircuitOpenError(self.name, self._remaining())
            if self._state is CircuitState.HALF_OPEN:
                if self._trial_in_progress:
                    raise CircuitOpenError(self.name, 0.0)
                self._trial_in_progress = True

    def _on_success(self):
        with self._lock:
            self._trial_in_progress = False
            if self._state is CircuitState.HALF_OPEN:
                self._transition(CircuitState.CLOSED, 'trial call succeeded')
            self._failures = 0

    def _on_failure(self, exc):
        with self._lock:
            self._trial_in_progress = False
            self._failures += 1
            reason = f'{type(exc).__name__}: {exc}'
            if self._state is CircuitState.HALF_OPEN:
                self._open(f'trial call failed ({reason})')
            elif self._state is CircuitState.CLOSED and self._failures >= self.failure_threshold:
                self._open(f'{self._failures} consecutive failures (last: {reason})')

    def _open(self, reason):
        self._opened_at = self._clock()
        self._transition(CircuitState.OPEN, reason)

    def _transition(self, new_state, reason):
        old_state = self._state
        self._state = new_state
        if new_state is CircuitState.CLOSED:
            self._opened_at = None
        if old_state is not new_state:
            event = {'at': datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
                     'from': old_state.value, 'to': new_state.value, 'reason': reason}
            self.transitions.append(event)
            logger.warning('circuit %s: %s -> %s (%s)', self.name, old_state.value, new_state.value, reason)
