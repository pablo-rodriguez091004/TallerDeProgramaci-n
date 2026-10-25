from dataclasses import dataclass
from datetime import datetime
from typing import Optional

USER_STATUSES = ('active', 'inactive')


@dataclass(kw_only=True)
class User:
    user_id: Optional[int] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    second_last_name: Optional[str] = None
    document_number: str
    email: str
    role: str
    password_hash: str
    phone: Optional[str] = None
    status: str = 'active'
    created_at: Optional[datetime] = None

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
