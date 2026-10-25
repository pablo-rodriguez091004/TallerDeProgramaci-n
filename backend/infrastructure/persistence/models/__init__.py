"""Modelos ORM (tablas). Importar este paquete registra todas las tablas en db.metadata."""

from infrastructure.persistence.models.user_model import User  # noqa: F401
from infrastructure.persistence.models.business_model import Business  # noqa: F401
from infrastructure.persistence.models.vehicle_model import Vehicle  # noqa: F401
from infrastructure.persistence.models.bay_model import Bay  # noqa: F401
from infrastructure.persistence.models.service_model import Service  # noqa: F401
from infrastructure.persistence.models.appointment_model import Appointment  # noqa: F401
from infrastructure.persistence.models.payment_model import Payment  # noqa: F401
from infrastructure.persistence.models.part_model import Part  # noqa: F401
from infrastructure.persistence.models.service_tracking_model import ServiceTracking  # noqa: F401
from infrastructure.persistence.models.service_tracking_parts_model import ServiceTrackingPart  # noqa: F401
from infrastructure.persistence.models.ai_call_model import AiCall  # noqa: F401
