from datetime import datetime

import pytest


@pytest.fixture
def fixed_now():
    """Reloj fijo: el resultado de las pruebas no depende de la hora real."""
    return datetime(2030, 1, 9, 15, 30)
