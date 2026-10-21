"""
La especificacion OpenAPI es parte del entregable: estas pruebas fallan si
deja de ser valida o si algun endpoint/campo queda sin documentar.
"""

import pytest
from openapi_spec_validator import validate

HTTP_METHODS = {'get', 'post', 'put', 'patch', 'delete'}


@pytest.fixture
def spec(app):
    response = app.test_client().get('/openapi.json')
    assert response.status_code == 200
    return response.get_json()


def _operations(spec):
    for path, item in spec['paths'].items():
        for method, operation in item.items():
            if method in HTTP_METHODS:
                yield f'{method.upper()} {path}', operation


def test_spec_is_valid_openapi_3(spec):
    assert spec['openapi'].startswith('3.')
    validate(spec)
    assert {'/api/v1/services', '/api/v1/services/{service_id}'} <= set(spec['paths'])


def test_every_operation_has_summary_description_and_examples(spec):
    for name, operation in _operations(spec):
        assert operation.get('summary'), f'{name} has no summary'
        assert operation.get('description'), f'{name} has no description'

        body = operation.get('requestBody')
        if body:
            assert 'example' in body['content']['application/json'], f'{name} request has no example'

        for status, response in operation['responses'].items():
            assert response.get('description'), f'{name} {status} has no description'
            if status != '204':
                assert 'example' in response['content']['application/json'], f'{name} {status} has no example'


def test_every_schema_field_has_description_and_example(spec):
    for schema_name, schema in spec['components']['schemas'].items():
        for field, definition in schema['properties'].items():
            assert definition.get('description'), f'{schema_name}.{field} has no description'
            assert 'example' in definition, f'{schema_name}.{field} has no example'


def test_swagger_ui_is_served(app):
    response = app.test_client().get('/docs')
    assert response.status_code == 200
    assert b'swagger-ui' in response.data
