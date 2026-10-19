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

La consulta de solapamiento vive en repositories/appointment_repository.py
(has_blocking_overlap) y se resuelve directamente en SQL.
"""

from repositories import appointment_repository, bay_repository, user_repository


def find_available_bay(business_id, scheduled_start, scheduled_end, exclude_appointment_id=None):
    """
    Devuelve la primera bahia del negocio que este disponible (status
    'available') y que no tenga ninguna cita bloqueante solapada con el
    horario pedido. Si ninguna bahia esta libre, devuelve None.
    """
    for bahia in bay_repository.list_by_business(business_id, only_available=True):
        tiene_choque = appointment_repository.has_blocking_overlap(
            scheduled_start, scheduled_end, bay_id=bahia.bay_id,
            exclude_appointment_id=exclude_appointment_id
        )
        if not tiene_choque:
            return bahia

    return None


def find_available_mechanic(scheduled_start, scheduled_end, exclude_appointment_id=None):
    """
    Devuelve el primer mecanico activo que no tenga ninguna cita bloqueante
    solapada con el horario pedido. Si ninguno esta libre, devuelve None.
    """
    for mecanico in user_repository.list_mechanics(only_active=True):
        tiene_choque = appointment_repository.has_blocking_overlap(
            scheduled_start, scheduled_end, mechanic_user_id=mecanico.user_id,
            exclude_appointment_id=exclude_appointment_id
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
