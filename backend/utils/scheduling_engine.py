"""
Motor de agendamiento.

Logica central para encontrar automaticamente una bahia y un mecanico
disponibles para una franja horaria, sin choque de horarios (solapamiento).

Regla de negocio (definida por Pablo en la sesion de diseño de base de datos):
la validacion de disponibilidad se resuelve aqui, en el backend, no con
constraints avanzados de PostgreSQL (como EXCLUDE) porque es la logica de
negocio central del sistema.

NOTA IMPORTANTE (simplificacion de arquitectura, a revisar con Pablo):
el esquema actual no tiene una tabla que asocie mecanicos a un negocio
especifico (users no tiene business_id). Como en la practica solo existe
UN negocio en los datos de prueba, este motor asume que CUALQUIER usuario
con rol 'mechanic' puede ser asignado, sin filtrar por negocio. Si el
proyecto llega a soportar varios talleres simultaneos, hara falta agregar
esa relacion (una tabla intermedia mechanics_businesses, o una columna
business_id en users) y filtrar aqui tambien por ella.
"""

from models.bay_model import Bay
from models.appointment_model import Appointment
from models.user_model import User

# Estados de cita que "ocupan" una bahia o un mecanico en el tiempo.
# Una cita cancelada o completada ya no bloquea ese horario.
BLOCKING_STATUSES = ('pending', 'confirmed', 'in_progress')


def _hay_solapamiento(inicio_existente, fin_existente, inicio_nuevo, fin_nuevo):
    """
    Dos franjas de tiempo [inicio, fin) se solapan si una empieza antes de
    que la otra termine, en ambos sentidos.
    """
    return inicio_existente < fin_nuevo and inicio_nuevo < fin_existente


def find_available_bay(business_id, scheduled_start, scheduled_end, exclude_appointment_id=None):
    """
    Devuelve la primera bahia del negocio que este disponible (status
    'available') y que no tenga ninguna cita bloqueante solapada con el
    horario pedido. Si ninguna bahia esta libre, devuelve None.
    """
    bahias = Bay.query.filter_by(business_id=business_id, status='available').all()

    for bahia in bahias:
        query = Appointment.query.filter(
            Appointment.bay_id == bahia.bay_id,
            Appointment.status.in_(BLOCKING_STATUSES)
        )
        if exclude_appointment_id:
            query = query.filter(Appointment.appointment_id != exclude_appointment_id)

        tiene_choque = any(
            _hay_solapamiento(cita.scheduled_start, cita.scheduled_end, scheduled_start, scheduled_end)
            for cita in query.all()
        )
        if not tiene_choque:
            return bahia

    return None


def find_available_mechanic(scheduled_start, scheduled_end, exclude_appointment_id=None):
    """
    Devuelve el primer mecanico activo que no tenga ninguna cita bloqueante
    solapada con el horario pedido. Si ninguno esta libre, devuelve None.
    """
    mecanicos = User.query.filter_by(role='mechanic', status='active').all()

    for mecanico in mecanicos:
        query = Appointment.query.filter(
            Appointment.mechanic_user_id == mecanico.user_id,
            Appointment.status.in_(BLOCKING_STATUSES)
        )
        if exclude_appointment_id:
            query = query.filter(Appointment.appointment_id != exclude_appointment_id)

        tiene_choque = any(
            _hay_solapamiento(cita.scheduled_start, cita.scheduled_end, scheduled_start, scheduled_end)
            for cita in query.all()
        )
        if not tiene_choque:
            return mecanico

    return None


def find_bay_and_mechanic(business_id, scheduled_start, scheduled_end, exclude_appointment_id=None):
    """
    Combina las dos busquedas anteriores. Solo tiene sentido crear la cita
    si HAY bahia Y mecanico disponibles simultaneamente para ese horario.
    """
    bahia = find_available_bay(business_id, scheduled_start, scheduled_end, exclude_appointment_id)
    if not bahia:
        return None, None

    mecanico = find_available_mechanic(scheduled_start, scheduled_end, exclude_appointment_id)
    if not mecanico:
        return None, None

    return bahia, mecanico
