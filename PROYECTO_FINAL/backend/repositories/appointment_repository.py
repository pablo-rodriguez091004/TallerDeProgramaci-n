from sqlalchemy.orm import joinedload
from db.conexion import db
from models.appointment_model import Appointment
from repositories import base_repository

# Estados de cita que "ocupan" una bahia o un mecanico en el tiempo.
# Una cita cancelada o completada ya no bloquea ese horario.
BLOCKING_STATUSES = ('pending', 'confirmed', 'in_progress')

# Relaciones que se cargan en la MISMA consulta (JOIN) al listar citas.
# Sin esto, serializar N citas dispararia hasta 5*N consultas extra (N+1).
_LIST_OPTIONS = (
    joinedload(Appointment.client),
    joinedload(Appointment.mechanic),
    joinedload(Appointment.vehicle),
    joinedload(Appointment.service),
    joinedload(Appointment.bay),
)


def get_by_id(appointment_id):
    return db.session.get(Appointment, appointment_id)


def get_detailed(appointment_id):
    return (Appointment.query.options(*_LIST_OPTIONS)
            .filter(Appointment.appointment_id == appointment_id)
            .first())


def list_for_user(user):
    """
    Cada rol ve un subconjunto distinto:
    - cliente: solo sus propias citas.
    - mecanico: solo las citas que tiene asignadas.
    - admin/owner: todas las citas del sistema.
    """
    query = Appointment.query.options(*_LIST_OPTIONS)
    if user.role == 'client':
        query = query.filter(Appointment.client_user_id == user.user_id)
    elif user.role == 'mechanic':
        query = query.filter(Appointment.mechanic_user_id == user.user_id)
    return query.order_by(Appointment.scheduled_start.desc()).all()


def has_blocking_overlap(scheduled_start, scheduled_end, bay_id=None, mechanic_user_id=None,
                         exclude_appointment_id=None):
    """
    True si existe una cita bloqueante de esa bahia (o de ese mecanico) que
    se solape con [scheduled_start, scheduled_end).

    Dos franjas [inicio, fin) se solapan si una empieza antes de que la otra
    termine, en ambos sentidos: existente.inicio < nuevo.fin y
    nuevo.inicio < existente.fin. La comparacion se hace en SQL, asi no se
    traen a memoria todas las citas de la bahia o del mecanico.
    """
    query = Appointment.query.filter(
        Appointment.status.in_(BLOCKING_STATUSES),
        Appointment.scheduled_start < scheduled_end,
        Appointment.scheduled_end > scheduled_start,
    )
    if bay_id is not None:
        query = query.filter(Appointment.bay_id == bay_id)
    if mechanic_user_id is not None:
        query = query.filter(Appointment.mechanic_user_id == mechanic_user_id)
    if exclude_appointment_id:
        query = query.filter(Appointment.appointment_id != exclude_appointment_id)
    return db.session.query(query.exists()).scalar()


def create(**fields):
    return base_repository.add(Appointment(**fields))
