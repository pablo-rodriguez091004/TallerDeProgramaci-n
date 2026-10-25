from domain.market_data.ports import HealthMonitor, SourceHealth


class BreakerHealthMonitor(HealthMonitor):
    """Expone el estado de cada circuit breaker como SourceHealth del dominio."""

    def __init__(self, breakers):
        self.breakers = breakers

    def health(self):
        return [SourceHealth(name=b.name, state=b.state.value, consecutive_failures=b.consecutive_failures,
                             failure_threshold=b.failure_threshold, recovery_timeout_s=b.recovery_timeout,
                             retry_in_s=b.retry_in(), transitions=list(b.transitions))
                for b in self.breakers]
