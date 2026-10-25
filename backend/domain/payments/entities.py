from dataclasses import dataclass
from datetime import datetime
from typing import Optional

PAYMENT_METHODS = ('cash', 'card', 'transfer')
PAYMENT_TYPES = ('deposit', 'balance')


@dataclass(kw_only=True)
class Payment:
    payment_id: Optional[int] = None
    appointment_id: int
    payment_type: str
    payment_method: str
    amount: int
    status: str = 'pending'
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    @property
    def is_completed(self):
        return self.status == 'completed'

    @property
    def is_deposit(self):
        return self.payment_type == 'deposit'

    def complete(self, payment_method, paid_at):
        """Pago simulado: no hay pasarela real conectada."""
        self.payment_method = payment_method
        self.status = 'completed'
        self.paid_at = paid_at
