"""
Exporta la especificacion OpenAPI de la API a docs/openapi.json y la valida
con openapi-spec-validator.

Uso (desde cualquier carpeta):
    backend/venv/bin/python scripts/export_openapi.py

No necesita base de datos: solo construye la app y lee el spec.
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND = os.path.join(ROOT, 'backend')
OUTPUT = os.path.join(ROOT, 'docs', 'openapi.json')
sys.path.insert(0, BACKEND)

from openapi_spec_validator import validate  # noqa: E402

from app import create_app  # noqa: E402
from api import api  # noqa: E402


def main():
    app = create_app()
    with app.app_context():
        spec = api.spec.to_dict()

    validate(spec)  # lanza OpenAPIValidationError si el documento no es valido

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
        f.write('\n')

    operations = sum(len(ops) for ops in spec['paths'].values())
    print(f"OpenAPI {spec['openapi']} valido: {len(spec['paths'])} rutas, {operations} operaciones")
    print(f'Exportado a {os.path.relpath(OUTPUT, ROOT)}')


if __name__ == '__main__':
    main()
