"""
Adaptadores de las fuentes de datos abiertos colombianas.

Endpoints verificados con llamadas reales el 2026-10-24 (ver docs/USO_DE_IA.md, Fase 3):

- datos.gov.co (Socrata SODA 2.1): https://www.datos.gov.co/resource/<id>.json
    u3vn-bdcy  CRECIMIENTO DEL PARQUE AUTOMOTOR RUNT2.0 (MinTransporte)
    gdxc-w37w  DIVIPOLA - Codigos municipios (DANE)
- Geoportal DANE (ArcGIS REST, servidor propio del DANE):
    INDICADORES_DE_POBLACION/Serv_Mpios_DistribucionPoblacionTotalCen_2018, capa 4
    (poblacion total censada por municipio, CNPV 2018)
"""

from domain.market_data.errors import DataSourceUnavailable
from domain.market_data.ports import PopulationSource, SourceInfo, TerritorySource, VehicleFleetSource
from infrastructure.resilience.http_client import (CircuitOpenError, PermanentHttpError, ResilientHttpClient,
                                                   RetryExhausted)

SOCRATA_BASE = 'https://www.datos.gov.co/resource'
DANE_POPULATION_LAYER = ('https://geoportal.dane.gov.co/mparcgis/rest/services/INDICADORES_DE_POBLACION/'
                         'Serv_Mpios_DistribucionPoblacionTotalCen_2018/MapServer/4')


def _fetch(source_key, call):
    """Traduce los errores tecnicos del cliente HTTP al error del dominio."""
    try:
        return call()
    except CircuitOpenError as exc:
        raise DataSourceUnavailable(source_key, str(exc), circuit_open=True) from exc
    except (RetryExhausted, PermanentHttpError) as exc:
        raise DataSourceUnavailable(source_key, str(exc)) from exc


class SocrataClient:
    """Lectura paginada de un dataset de datos.gov.co con consultas SoQL."""

    def __init__(self, http: ResilientHttpClient, base_url=SOCRATA_BASE, page_size=50000, app_token=None):
        self.http = http
        self.base_url = base_url.rstrip('/')
        self.page_size = page_size
        self.app_token = app_token

    def dataset_url(self, dataset_id):
        return f'{self.base_url}/{dataset_id}.json'

    def rows(self, dataset_id, soql):
        """Todas las filas de la consulta, pagina por pagina ($limit/$offset con $order estable)."""
        rows, offset = [], 0
        while True:
            params = {**soql, '$limit': self.page_size, '$offset': offset}
            if self.app_token:
                params['$$app_token'] = self.app_token
            page = self.http.get_json(self.dataset_url(dataset_id), params)
            if not isinstance(page, list):
                raise PermanentHttpError(200, f'{dataset_id}: expected a JSON array')
            rows.extend(page)
            if len(page) < self.page_size:
                return rows
            offset += self.page_size


class RuntFleetSource(VehicleFleetSource):
    """
    Parque automotor ACTIVO agregado en el servidor por departamento, clase y
    año de registro: 28 mil filas (~3 MB) en vez de 192 mil filas (~27 MB).
    El detalle por municipio no se usa en el analisis.
    """
    DATASET = 'u3vn-bdcy'

    def __init__(self, socrata: SocrataClient):
        self.socrata = socrata
        self.info = SourceInfo('runt_fleet', 'Crecimiento del parque automotor RUNT 2.0',
                               'Ministerio de Transporte (datos.gov.co)', socrata.dataset_url(self.DATASET))

    def fetch(self):
        soql = {
            '$select': 'nombre_departamento, nombre_de_la_clase, fecha_de_registro, '
                       'sum(cantidad) as vehiculos, max(mes_de_publicacion) as mes_publicacion, '
                       'max(a_o_de_publicacion) as anio_publicacion',
            '$where': "estado_del_vehiculo = 'ACTIVO'",
            '$group': 'nombre_departamento, nombre_de_la_clase, fecha_de_registro',
            '$order': 'nombre_departamento, nombre_de_la_clase, fecha_de_registro',
        }
        return _fetch(self.info.key, lambda: self.socrata.rows(self.DATASET, soql))


class DivipolaSource(TerritorySource):
    DATASET = 'gdxc-w37w'

    def __init__(self, socrata: SocrataClient):
        self.socrata = socrata
        self.info = SourceInfo('divipola', 'DIVIPOLA - Códigos municipios',
                               'DANE (datos.gov.co)', socrata.dataset_url(self.DATASET))

    def fetch(self):
        soql = {'$select': 'cod_dpto, dpto, cod_mpio, nom_mpio, tipo_municipio', '$order': 'cod_mpio'}
        return _fetch(self.info.key, lambda: self.socrata.rows(self.DATASET, soql))


class DanePopulationSource(PopulationSource):
    """
    Capa ArcGIS del geoportal del DANE. ArcGIS responde HTTP 200 incluso ante
    errores ({"error": {...}}) y pagina con resultOffset cuando el resultado
    supera maxRecordCount (2000): ambos casos se manejan aqui.
    """

    def __init__(self, http: ResilientHttpClient, layer_url=DANE_POPULATION_LAYER, page_size=2000):
        self.http = http
        self.layer_url = layer_url
        self.page_size = page_size
        self.info = SourceInfo('dane_population', 'Población total censada por municipio (CNPV 2018)',
                               'DANE (geoportal.dane.gov.co)', f'{layer_url}/query')

    def _all_features(self):
        features, offset = [], 0
        while True:
            data = self.http.get_json(f'{self.layer_url}/query', {
                'where': '1=1', 'outFields': 'DPTO_CCDGO,MPIO_CCDGO,MPIO_CNMBR,CL0_TT_PERSN',
                'returnGeometry': 'false', 'orderByFields': 'MPIO_CCDGO',
                'resultOffset': offset, 'resultRecordCount': self.page_size, 'f': 'json'})
            if 'error' in data:
                raise PermanentHttpError(data['error'].get('code', 200), f'{self.layer_url}: {data["error"]}')
            page = data.get('features', [])
            features.extend(page)
            if not data.get('exceededTransferLimit') or not page:
                return features
            offset += len(page)

    def fetch(self):
        features = _fetch(self.info.key, self._all_features)
        return [{'cod_dpto': f['attributes']['DPTO_CCDGO'], 'cod_mpio': f['attributes']['MPIO_CCDGO'],
                 'municipio': (f['attributes']['MPIO_CNMBR'] or '').strip(),
                 'poblacion': f['attributes']['CL0_TT_PERSN']} for f in features]
