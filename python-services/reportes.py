"""
Microservicio de reportes.

Reutiliza directamente los modelos SQLAlchemy definidos en backend/models
(Usuario, Espacio, Reserva, Pago) en lugar de redefinir el acceso a datos,
cumpliendo el requerimiento de reutilización de código: la app Flask y
este microservicio comparten exactamente la misma capa de persistencia.

Uso:
    cd PROYECTO_FINAL/python-services
    python reportes.py
"""

import os
import sys
from datetime import date, datetime, timedelta

# Reutiliza la carpeta backend/ como raíz de imports (mismo esquema
# que usa "cd backend && python app.py"), evitando así duplicar la
# app factory, la conexión a base de datos y los modelos.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app import create_app                     # reutiliza la app factory del backend
from db.conexion import db                      # misma instancia de SQLAlchemy
from models import Usuario, Espacio, Reserva, Pago   # mismos modelos que la API


def reporte_ocupacion_por_espacio(fecha_inicio: date, fecha_fin: date):
    """Cuenta cuántas reservas confirmadas/completadas tuvo cada espacio
    en un rango de fechas, y las horas totales reservadas."""
    espacios = Espacio.query.all()
    reporte = []

    for espacio in espacios:
        reservas = Reserva.query.filter(
            Reserva.id_espacio == espacio.id_espacio,
            Reserva.fecha_reserva.between(fecha_inicio, fecha_fin),
            Reserva.estado.in_(["confirmada", "completada"]),
        ).all()

        horas_totales = 0
        for r in reservas:
            inicio = datetime.combine(date.min, r.hora_inicio)
            fin = datetime.combine(date.min, r.hora_fin)
            horas_totales += (fin - inicio).total_seconds() / 3600

        reporte.append({
            "espacio": espacio.nombre,
            "tipo": espacio.tipo,
            "numero_reservas": len(reservas),
            "horas_reservadas": round(horas_totales, 1),
            "ingresos_estimados": round(horas_totales * float(espacio.precio_hora), 2),
        })

    return sorted(reporte, key=lambda r: r["numero_reservas"], reverse=True)


def reporte_ingresos(fecha_inicio: date, fecha_fin: date):
    """Suma el monto de los pagos registrados en el rango de fechas,
    agrupado por método de pago."""
    pagos = Pago.query.filter(
        Pago.fecha_pago >= datetime.combine(fecha_inicio, datetime.min.time()),
        Pago.fecha_pago <= datetime.combine(fecha_fin, datetime.max.time()),
        Pago.estado == "pagado",
    ).all()

    resumen = {}
    for pago in pagos:
        resumen.setdefault(pago.metodo_pago, 0)
        resumen[pago.metodo_pago] += float(pago.monto)

    resumen["total"] = sum(resumen.values())
    return resumen


def imprimir_reporte(fecha_inicio: date, fecha_fin: date):
    print(f"\n=== Reporte de ocupación ({fecha_inicio} a {fecha_fin}) ===")
    for fila in reporte_ocupacion_por_espacio(fecha_inicio, fecha_fin):
        print(
            f"- {fila['espacio']} ({fila['tipo']}): "
            f"{fila['numero_reservas']} reservas, "
            f"{fila['horas_reservadas']} h, "
            f"ingresos est. ${fila['ingresos_estimados']:,.0f}"
        )

    print(f"\n=== Reporte de ingresos por método de pago ===")
    for metodo, monto in reporte_ingresos(fecha_inicio, fecha_fin).items():
        print(f"- {metodo}: ${monto:,.0f}")


if __name__ == "__main__":
    # Usa la misma app factory y configuración que el backend (config.py),
    # así que se conecta a la MISMA base de datos PostgreSQL sin duplicar credenciales.
    app = create_app()
    with app.app_context():
        hoy = date.today()
        hace_30_dias = hoy - timedelta(days=30)
        imprimir_reporte(hace_30_dias, hoy)