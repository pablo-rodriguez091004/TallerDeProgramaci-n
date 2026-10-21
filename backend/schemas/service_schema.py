"""
Esquemas Marshmallow del catalogo de servicios (/api/v1/services).

Cada campo lleva description y example en ingles: flask-smorest los copia a
la especificacion OpenAPI y Swagger UI los muestra.
"""

from marshmallow import Schema, fields, pre_load, validate

SERVICE_STATUSES = ('active', 'inactive')


class ServiceSchema(Schema):
    """Representacion de salida de un servicio."""

    service_id = fields.Integer(dump_only=True, metadata={
        'description': 'Unique identifier of the service.', 'example': 1})
    business_id = fields.Integer(dump_only=True, metadata={
        'description': 'Identifier of the workshop that offers the service.', 'example': 1})
    service_name = fields.String(metadata={
        'description': 'Unique service name within the workshop.', 'example': 'Cambio de aceite'})
    description = fields.String(allow_none=True, metadata={
        'description': 'What the service includes.', 'example': 'Cambio de aceite y filtro'})
    estimated_duration_minutes = fields.Integer(metadata={
        'description': 'Estimated time the vehicle occupies a bay, in minutes.', 'example': 45})
    base_price = fields.Integer(metadata={
        'description': 'Base price in Colombian pesos (COP), without decimals.', 'example': 80000})
    status = fields.String(metadata={
        'description': "Catalog status: 'active' services can be booked.", 'example': 'active'})


class ServiceInputSchema(Schema):
    """Cuerpo de POST y PUT. PUT exige la representacion completa (no es un PATCH)."""

    service_name = fields.String(required=True, validate=validate.Length(min=2, max=100), metadata={
        'description': 'Service name (2-100 characters). Must be unique within the workshop, case-insensitive.',
        'example': 'Cambio de pastillas de freno'})
    description = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=500), metadata={
        'description': 'Optional description of what the service includes (max 500 characters).',
        'example': 'Reemplazo de pastillas delanteras y revision de discos'})
    estimated_duration_minutes = fields.Integer(required=True, strict=True, validate=validate.Range(min=5, max=600),
                                                metadata={
        'description': 'Estimated duration in minutes (5-600).', 'example': 90})
    base_price = fields.Integer(required=True, strict=True, validate=validate.Range(min=0, max=100_000_000), metadata={
        'description': 'Base price in COP, integer between 0 and 100,000,000.', 'example': 150000})
    status = fields.String(load_default='active', validate=validate.OneOf(SERVICE_STATUSES), metadata={
        'description': "Catalog status, 'active' (default) or 'inactive'.", 'example': 'active'})

    @pre_load
    def strip_strings(self, data, **kwargs):
        # "   " no debe pasar como nombre valido.
        if isinstance(data, dict):
            data = dict(data)
            for key in ('service_name', 'description'):
                if isinstance(data.get(key), str):
                    data[key] = data[key].strip()
        return data


class ServiceQuerySchema(Schema):
    status = fields.String(load_default='active', validate=validate.OneOf(SERVICE_STATUSES + ('all',)), metadata={
        'description': "Filter by status: 'active' (default), 'inactive' or 'all'.", 'example': 'active'})
