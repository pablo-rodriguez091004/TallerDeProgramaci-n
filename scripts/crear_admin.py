"""
Crea (si no existe) el usuario ADMINISTRADOR de prueba en la base configurada
en backend/.env: administra el negocio, la recepcion de clientes, el
inventario y la agenda.

    backend/venv/bin/python scripts/crear_admin.py

Correo: admin@tallermecanico.com · contraseña: test1234 (cambiala en produccion).
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'backend'))

from app import create_app  # noqa: E402
from domain.shared.errors import Conflict  # noqa: E402

ADMIN = {'first_name': 'Administrador', 'last_name': 'Taller', 'document_number': '1004567890',
         'email': 'admin@tallermecanico.com', 'password': 'test1234', 'phone': '3034567890'}

app = create_app()
with app.app_context():
    try:
        user = app.extensions['mecatrack'].auth.register(ADMIN, role='admin')
        print(f"Creado: {user.email} (rol {user.role}, id {user.user_id}) · contraseña test1234")
    except Conflict as exc:
        print(f"No se creo: {exc.message} ({ADMIN['email']} / documento {ADMIN['document_number']})")
