"""Caso de uso: actualizar y consultar los datos abiertos que usa el analisis de mercado."""

import time
from dataclasses import dataclass
from typing import Optional

from domain.market_data.errors import DataSourceUnavailable
from domain.market_data.ports import DataSource, HealthMonitor, SnapshotStore
from domain.shared.ports import Clock


@dataclass
class RefreshResult:
    source: str
    title: str
    publisher: str
    url: str
    ok: bool
    rows: Optional[int] = None
    elapsed_ms: Optional[int] = None
    error: Optional[str] = None
    circuit_open: bool = False


class MarketDataService:

    def __init__(self, sources: list[DataSource], store: SnapshotStore, health: HealthMonitor, clock: Clock,
                 timer=time.perf_counter):
        self._sources = sources
        self._store = store
        self._health = health
        self._clock = clock
        self._timer = timer

    def refresh(self):
        """
        Descarga cada fuente y guarda su snapshot. Una fuente caida no
        detiene a las demas: se reporta y se conserva su snapshot anterior.
        """
        results = []
        for source in self._sources:
            info = source.info
            started = self._timer()
            try:
                records = source.fetch()
            except DataSourceUnavailable as exc:
                results.append(RefreshResult(info.key, info.title, info.publisher, info.url, ok=False,
                                             elapsed_ms=round((self._timer() - started) * 1000),
                                             error=exc.message, circuit_open=exc.circuit_open))
                continue
            snapshot = self._store.save(info.key, records, self._clock.now())
            results.append(RefreshResult(info.key, info.title, info.publisher, info.url, ok=True,
                                         rows=snapshot.rows, elapsed_ms=round((self._timer() - started) * 1000)))
        return results

    def snapshots(self):
        return {source.info.key: self._store.latest(source.info.key) for source in self._sources}

    def sources(self):
        return [source.info for source in self._sources]

    def health(self):
        return self._health.health()
