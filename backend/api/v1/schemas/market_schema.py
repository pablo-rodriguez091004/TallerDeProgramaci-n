"""
Esquemas de /api/v1/market (datos abiertos colombianos + analisis DuckDB).

Los ejemplos son valores REALES de la ejecucion del 2026-10-24 (RUNT corte
octubre 2026, CNPV 2018), para que Swagger UI muestre datos verosimiles.
"""

from marshmallow import Schema, fields

# --- Ejemplos (salida real) ----------------------------------------------------------------

FLEET_AGE_ROW = {'clase': 'MOTOCICLETA', 'tipo_taller': 'motorcycle', 'vehiculos': 14512606, 'media': 10.85,
                 'desviacion': 9.23, 'minimo': 0, 'p25': 4, 'mediana': 9, 'p75': 16, 'p90': 22, 'maximo': 76,
                 'pct_10_anios_o_mas': 49.8}
TRANSITION_EXAMPLE = {'at': '2026-10-25T01:53:28.416+00:00', 'from': 'CLOSED', 'to': 'OPEN',
                      'reason': '3 consecutive failures (last: TransientHttpError: timeout calling ...)'}
CIRCUIT_EXAMPLE = {'name': 'datos.gov.co', 'state': 'CLOSED', 'consecutive_failures': 0, 'failure_threshold': 3,
                   'recovery_timeout_s': 30.0, 'retry_in_s': None, 'transitions': []}


class ColumnSchema(Schema):
    key = fields.String(metadata={'description': 'Key of the value inside each row.', 'example': 'mediana'})
    label = fields.String(metadata={'description': 'Column header to display (Spanish).', 'example': 'Mediana'})
    type = fields.String(metadata={'description': "'number' or 'text', to align and format the cell.",
                                   'example': 'number'})


class AnalyticsResultSchema(Schema):
    name = fields.String(metadata={'description': 'Identifier of the analytical query.',
                                   'example': 'fleet_age_by_class'})
    title = fields.String(metadata={'description': 'Human-readable title (Spanish).',
                                    'example': 'Antigüedad del parque automotor activo por clase'})
    description = fields.String(metadata={'description': 'What the numbers mean and their caveats.',
                                          'example': 'Años desde el registro (corte RUNT OCTUBRE 2026), ponderado '
                                                     'por número de vehículos.'})
    columns = fields.List(fields.Nested(ColumnSchema), metadata={
        'description': 'Ordered columns of `rows`.',
        'example': [{'key': 'clase', 'label': 'Clase', 'type': 'text'},
                    {'key': 'mediana', 'label': 'Mediana', 'type': 'number'}]})
    rows = fields.List(fields.Dict(), metadata={'description': 'Result rows computed by DuckDB.',
                                                'example': [FLEET_AGE_ROW]})
    summary = fields.Dict(metadata={'description': 'Aggregated descriptive statistics of the result.',
                                    'example': {'vehiculos_analizados': 22054289,
                                                'antiguedad_media_ponderada': 13.38, 'excluidos_por_calidad': 8864}})
    sql = fields.String(metadata={'description': 'Exact DuckDB SQL that produced the rows (for transparency).',
                                  'example': 'WITH clases_taller(clase, tipo_taller) AS (VALUES ...) SELECT ...'})
    elapsed_ms = fields.Float(metadata={'description': 'DuckDB execution time of the main query, in ms.',
                                        'example': 89.5})
    snapshots = fields.Dict(metadata={'description': 'Download time (UTC) of each open-data snapshot used.',
                                      'example': {'runt_fleet': '2026-10-25T01:59:11.703291'}})


class TransitionSchema(Schema):
    at = fields.String(metadata={'description': 'When the transition happened (ISO 8601, UTC).',
                                 'example': TRANSITION_EXAMPLE['at']})
    from_ = fields.String(data_key='from', metadata={'description': 'Previous state.', 'example': 'CLOSED'})
    to = fields.String(metadata={'description': 'New state.', 'example': 'OPEN'})
    reason = fields.String(metadata={'description': 'Why the breaker changed state.',
                                     'example': TRANSITION_EXAMPLE['reason']})


class CircuitSchema(Schema):
    name = fields.String(metadata={'description': 'External dependency (host) protected by the breaker.',
                                   'example': 'datos.gov.co'})
    state = fields.String(metadata={'description': 'CLOSED (calls pass), OPEN (calls rejected) or HALF_OPEN '
                                                   '(one trial call allowed).', 'example': 'CLOSED'})
    consecutive_failures = fields.Integer(metadata={'description': 'Failures in a row counted by the breaker.',
                                                    'example': 0})
    failure_threshold = fields.Integer(metadata={'description': 'Failures in a row that open the circuit.',
                                                 'example': 3})
    recovery_timeout_s = fields.Float(metadata={'description': 'Seconds OPEN before allowing a trial call.',
                                                'example': 30.0})
    retry_in_s = fields.Float(allow_none=True, metadata={
        'description': 'Seconds until the next trial call (only when OPEN).', 'example': None})
    transitions = fields.List(fields.Nested(TransitionSchema), metadata={
        'description': 'Last state changes, oldest first.', 'example': [TRANSITION_EXAMPLE]})


class SourceStatusSchema(Schema):
    key = fields.String(metadata={'description': 'Short name of the source.', 'example': 'runt_fleet'})
    title = fields.String(metadata={'description': 'Dataset title.',
                                    'example': 'Crecimiento del parque automotor RUNT 2.0'})
    publisher = fields.String(metadata={'description': 'Publishing entity and platform.',
                                        'example': 'Ministerio de Transporte (datos.gov.co)'})
    url = fields.String(metadata={'description': 'Endpoint queried.',
                                  'example': 'https://www.datos.gov.co/resource/u3vn-bdcy.json'})
    fetched_at = fields.String(allow_none=True, metadata={
        'description': 'Last successful download (UTC), null if never downloaded.',
        'example': '2026-10-25T01:59:11.703291'})
    rows = fields.Integer(allow_none=True, metadata={'description': 'Records in the last download.',
                                                     'example': 28007})


class SourcesResponseSchema(Schema):
    sources = fields.List(fields.Nested(SourceStatusSchema), metadata={
        'description': 'Open-data sources and their last snapshot.',
        'example': [{'key': 'runt_fleet', 'title': 'Crecimiento del parque automotor RUNT 2.0',
                     'publisher': 'Ministerio de Transporte (datos.gov.co)',
                     'url': 'https://www.datos.gov.co/resource/u3vn-bdcy.json',
                     'fetched_at': '2026-10-25T01:59:11.703291', 'rows': 28007}]})
    circuits = fields.List(fields.Nested(CircuitSchema), metadata={
        'description': 'Circuit breaker of each external host.', 'example': [CIRCUIT_EXAMPLE]})


class RefreshResultSchema(Schema):
    source = fields.String(metadata={'description': 'Short name of the source.', 'example': 'runt_fleet'})
    title = fields.String(metadata={'description': 'Dataset title.',
                                    'example': 'Crecimiento del parque automotor RUNT 2.0'})
    publisher = fields.String(metadata={'description': 'Publishing entity.',
                                        'example': 'Ministerio de Transporte (datos.gov.co)'})
    url = fields.String(metadata={'description': 'Endpoint queried.',
                                  'example': 'https://www.datos.gov.co/resource/u3vn-bdcy.json'})
    ok = fields.Boolean(metadata={'description': 'Whether the download succeeded.', 'example': True})
    rows = fields.Integer(allow_none=True, metadata={'description': 'Records downloaded.', 'example': 28007})
    elapsed_ms = fields.Integer(allow_none=True, metadata={'description': 'Time spent, retries included.',
                                                           'example': 1372})
    error = fields.String(allow_none=True, metadata={'description': 'Failure reason, null on success.',
                                                     'example': None})
    circuit_open = fields.Boolean(metadata={'description': 'True if rejected because the circuit is OPEN.',
                                            'example': False})


class RefreshResponseSchema(Schema):
    results = fields.List(fields.Nested(RefreshResultSchema), metadata={
        'description': 'One result per source; a failing source does not stop the others.',
        'example': [{'source': 'runt_fleet', 'title': 'Crecimiento del parque automotor RUNT 2.0',
                     'publisher': 'Ministerio de Transporte (datos.gov.co)',
                     'url': 'https://www.datos.gov.co/resource/u3vn-bdcy.json', 'ok': True, 'rows': 28007,
                     'elapsed_ms': 1372, 'error': None, 'circuit_open': False}]})
    circuits = fields.List(fields.Nested(CircuitSchema), metadata={
        'description': 'Circuit breakers after the refresh.', 'example': [CIRCUIT_EXAMPLE]})
