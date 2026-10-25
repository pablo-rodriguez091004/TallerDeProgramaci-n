from abc import ABC, abstractmethod
from typing import Optional

from domain.catalog.entities import Bay, Business, Part, Service, Vehicle


class BusinessRepository(ABC):
    @abstractmethod
    def get_by_owner(self, owner_user_id: int) -> Optional[Business]: ...

    @abstractmethod
    def first(self) -> Optional[Business]:
        """El primer taller registrado (hoy el sistema tiene uno solo)."""

    @abstractmethod
    def save(self, business: Business) -> None: ...


class BayRepository(ABC):
    @abstractmethod
    def get(self, bay_id: int) -> Optional[Bay]: ...

    @abstractmethod
    def get_by_number(self, business_id: int, bay_number: str) -> Optional[Bay]: ...

    @abstractmethod
    def list_by_business(self, business_id: int, only_available: bool = False) -> list[Bay]: ...

    @abstractmethod
    def add(self, bay: Bay) -> Bay: ...

    @abstractmethod
    def save(self, bay: Bay) -> None: ...


class ServiceRepository(ABC):
    @abstractmethod
    def get(self, service_id: int) -> Optional[Service]: ...

    @abstractmethod
    def list_active(self) -> list[Service]: ...

    @abstractmethod
    def list_by_business(self, business_id: int) -> list[Service]: ...

    @abstractmethod
    def list_by_status(self, status: Optional[str] = None) -> list[Service]: ...

    @abstractmethod
    def find_by_name(self, business_id: int, service_name: str,
                     exclude_id: Optional[int] = None) -> Optional[Service]:
        """Mismo nombre en el taller, sin distinguir mayusculas."""

    @abstractmethod
    def count_appointments(self, service_id: int) -> int: ...

    @abstractmethod
    def add(self, service: Service) -> Service: ...

    @abstractmethod
    def save(self, service: Service) -> None: ...

    @abstractmethod
    def delete(self, service_id: int) -> None: ...


class PartRepository(ABC):
    @abstractmethod
    def get(self, part_id: int) -> Optional[Part]: ...

    @abstractmethod
    def list_by_business(self, business_id: int, include_inactive: bool = False) -> list[Part]: ...

    @abstractmethod
    def add(self, part: Part) -> Part: ...

    @abstractmethod
    def save(self, part: Part) -> None: ...


class VehicleRepository(ABC):
    @abstractmethod
    def get(self, vehicle_id: int) -> Optional[Vehicle]: ...

    @abstractmethod
    def get_by_plate(self, license_plate: str) -> Optional[Vehicle]: ...

    @abstractmethod
    def list_by_owner(self, owner_user_id: int) -> list[Vehicle]: ...

    @abstractmethod
    def has_appointments(self, vehicle_id: int) -> bool: ...

    @abstractmethod
    def add(self, vehicle: Vehicle) -> Vehicle: ...

    @abstractmethod
    def save(self, vehicle: Vehicle) -> None: ...

    @abstractmethod
    def delete(self, vehicle_id: int) -> None: ...
