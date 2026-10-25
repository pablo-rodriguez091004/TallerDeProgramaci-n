"""Gestion del negocio: el taller y lo que ofrece o administra."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

BAY_STATUSES = ('available', 'under_maintenance')
ACTIVE_STATUSES = ('active', 'inactive')


@dataclass(kw_only=True)
class Business:
    business_id: Optional[int] = None
    business_name: str
    tax_id: str
    address: str
    business_phone: Optional[str] = None
    business_registration_number: Optional[str] = None
    legal_documents_verified: bool = False
    owner_user_id: int


@dataclass(kw_only=True)
class Bay:
    bay_id: Optional[int] = None
    business_id: int
    bay_number: str
    has_elevator: bool = False
    status: str = 'available'


@dataclass(kw_only=True)
class Service:
    service_id: Optional[int] = None
    business_id: int
    service_name: str
    description: Optional[str] = None
    estimated_duration_minutes: int
    base_price: int
    status: str = 'active'

    @property
    def is_bookable(self):
        return self.status == 'active'


@dataclass(kw_only=True)
class Part:
    part_id: Optional[int] = None
    business_id: int
    part_name: str
    unit_price: int
    stock_quantity: int = 0
    status: str = 'active'


@dataclass(kw_only=True)
class Vehicle:
    vehicle_id: Optional[int] = None
    owner_user_id: int
    license_plate: str
    brand: str
    model: str
    year: int
    color: Optional[str] = None
    vehicle_type: str
    vin: Optional[str] = None
    engine_displacement: Optional[Decimal] = None
    mileage: Optional[int] = None
    fuel_type: str
    transmission_type: str
