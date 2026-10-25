"""
Configuracion comun de pytest.

- tests/unit/:        sin base de datos ni red; dependencias simuladas con unittest.mock.
- tests/integration/: Flask + PostgreSQL reales (fixtures en su propio conftest.py).
"""

import os
import sys

# backend/ en el path: los tests importan app, domain, application, ...
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
