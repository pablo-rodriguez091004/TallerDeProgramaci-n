import os
from dotenv import load_dotenv

# Carga backend/.env aunque el proceso se lance desde otra carpeta
# (por ejemplo, flask db upgrade desde la raiz o los scripts de scripts/).
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


def _default_test_database_url():
    """
    Si no se define TEST_DATABASE_URL, reutiliza las credenciales de
    DATABASE_URL pero apuntando a la base 'taller_mecanico_test'.
    """
    from sqlalchemy.engine import make_url
    base = os.environ.get('DATABASE_URL')
    if not base:
        return None
    return make_url(base).set(database='taller_mecanico_test').render_as_string(hide_password=False)


class TestConfig(Config):
    """
    Configuracion de pruebas: usa SIEMPRE una base aparte (TEST_DATABASE_URL),
    nunca la de desarrollo. tests/conftest.py se niega a correr si el nombre
    de la base no termina en '_test'.
    """
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or _default_test_database_url()
