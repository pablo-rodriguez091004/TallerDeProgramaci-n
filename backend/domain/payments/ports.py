from abc import ABC, abstractmethod
from typing import Optional

from domain.payments.entities import Payment


class PaymentRepository(ABC):
    @abstractmethod
    def get(self, payment_id: int) -> Optional[Payment]: ...

    @abstractmethod
    def list_by_appointment(self, appointment_id: int) -> list[Payment]: ...

    @abstractmethod
    def add(self, payment: Payment) -> Payment: ...

    @abstractmethod
    def save(self, payment: Payment) -> None: ...
