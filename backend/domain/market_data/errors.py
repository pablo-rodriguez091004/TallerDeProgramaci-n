from domain.shared.errors import Conflict


class DataSourceUnavailable(Exception):
    """
    Una fuente externa no respondio (fallo de red, HTTP 5xx, circuito
    abierto, ...). Los adaptadores traducen sus errores tecnicos a esta
    excepcion para que la aplicacion no dependa de httpx ni del breaker.
    """

    def __init__(self, source, message, circuit_open=False):
        super().__init__(f'{source}: {message}')
        self.source = source
        self.message = message
        self.circuit_open = circuit_open


class SnapshotMissing(Conflict):
    """Todavia no se descargaron los datos abiertos que necesita el analisis."""
    default_code = 'market_data_not_loaded'

    def __init__(self, missing):
        super().__init__(f"Open data not downloaded yet: {', '.join(missing)}. Run POST /api/v1/market/refresh first.",
                         details={'missing_sources': list(missing)})
