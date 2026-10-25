"""
Datos de mercado: fuentes publicas colombianas que dan contexto al taller.

Cada fuente devuelve los registros JSON tal como los entrega la API (lista
de dicts); el analisis lo hace el motor analitico (DuckDB) en la Fase 4.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class SourceInfo:
    key: str          # nombre corto: 'runt_fleet', 'dane_population', 'divipola'
    title: str
    publisher: str
    url: str          # endpoint consultado


class DataSource(ABC):
    info: SourceInfo

    @abstractmethod
    def fetch(self) -> list[dict]:
        """Descarga los registros. Lanza DataSourceUnavailable si la fuente falla."""


class VehicleFleetSource(DataSource):
    """Parque automotor activo agregado por departamento, clase y año de registro."""


class PopulationSource(DataSource):
    """Poblacion censada por municipio (codigo DIVIPOLA)."""


class TerritorySource(DataSource):
    """Division politico-administrativa: codigos y nombres de departamentos y municipios."""


@dataclass
class Snapshot:
    source: str
    fetched_at: datetime
    rows: int
    path: str


@dataclass
class SourceHealth:
    """Estado de la dependencia externa (lo expone el circuit breaker)."""
    name: str
    state: str                      # CLOSED | OPEN | HALF_OPEN
    consecutive_failures: int
    failure_threshold: int
    recovery_timeout_s: float
    retry_in_s: Optional[float] = None
    transitions: list[dict] = field(default_factory=list)


class SnapshotStore(ABC):
    @abstractmethod
    def save(self, source: str, records: list[dict], fetched_at: datetime) -> Snapshot: ...

    @abstractmethod
    def latest(self, source: str) -> Optional[Snapshot]: ...


class HealthMonitor(ABC):
    @abstractmethod
    def health(self) -> list[SourceHealth]: ...


@dataclass
class AnalyticsResult:
    """Resultado tabular de una consulta analitica, listo para tabla y grafico."""
    name: str
    title: str
    description: str
    columns: list[dict]             # [{'key', 'label', 'type'}]
    rows: list[dict]
    summary: dict
    sql: str
    elapsed_ms: float
    snapshots: dict                 # fuente -> fecha de descarga (ISO)


class MarketAnalytics(ABC):
    """Motor analitico sobre los snapshots descargados (DuckDB en infraestructura)."""

    @abstractmethod
    def fleet_age_by_class(self) -> AnalyticsResult: ...

    @abstractmethod
    def motorization_by_department(self) -> AnalyticsResult: ...

    @abstractmethod
    def age_distribution(self) -> AnalyticsResult: ...
