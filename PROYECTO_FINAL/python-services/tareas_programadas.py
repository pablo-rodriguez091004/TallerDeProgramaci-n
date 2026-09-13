"""
Tareas programadas del sistema.

Igual que reportes.py, reutiliza la app factory y los modelos del
backend en lugar de duplicar la conexión a base de datos o las
clases de las entidades.

Pensado para ejecutarse periódicamente (cron, Task Scheduler o un
job de APScheduler) para mantener consistente el estado de las reservas.
"""

import os
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app import create_app
from db.conexion import db
from models import Reserva


def liberar_reservas_pendientes_vencidas(horas_limite: int = 24):
    """Si una reserva sigue 'pendiente' (sin pago) más de `horas_limite`
    horas después de haberse creado, se cancela automáticamente para
    liberar el espacio a otros clientes."""
    limite = datetime.now(timezone.utc) - timedelta(hours=horas_limite)

    vencidas = Reserva.query.filter(
        Reserva.estado == "pendiente",
        Reserva.fecha_creacion <= limite,
    ).all()

    for reserva in vencidas:
        reserva.estado = "cancelada"

    if vencidas:
        db.session.commit()

    print(f"[tareas_programadas] {len(vencidas)} reserva(s) pendiente(s) vencida(s) liberada(s).")
    return len(vencidas)


def marcar_reservas_completadas():
    """Marca como 'completada' toda reserva confirmada cuya fecha ya pasó,
    para mantener el historial y los reportes al día."""
    hoy = date.today()

    a_completar = Reserva.query.filter(
        Reserva.estado == "confirmada",
        Reserva.fecha_reserva < hoy,
    ).all()

    for reserva in a_completar:
        reserva.estado = "completada"

    if a_completar:
        db.session.commit()

    print(f"[tareas_programadas] {len(a_completar)} reserva(s) marcada(s) como completada(s).")
    return len(a_completar)


def ejecutar_tareas_diarias():
    liberar_reservas_pendientes_vencidas()
    marcar_reservas_completadas()


if __name__ == "__main__":
    # Reutiliza la MISMA app/config/modelos que el backend Flask y que reportes.py
    app = create_app()
    with app.app_context():
        ejecutar_tareas_diarias()