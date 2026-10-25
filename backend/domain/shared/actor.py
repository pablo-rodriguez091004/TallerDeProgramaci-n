from dataclasses import dataclass

ROLES = ('client', 'mechanic', 'admin', 'owner')
STAFF_ROLES = ('mechanic', 'admin', 'owner')
MANAGER_ROLES = ('owner', 'admin')


@dataclass(frozen=True)
class Actor:
    """Quien ejecuta el caso de uso. La api lo construye desde la sesion."""
    user_id: int
    role: str

    @property
    def is_client(self):
        return self.role == 'client'

    @property
    def is_mechanic(self):
        return self.role == 'mechanic'

    @property
    def is_manager(self):
        return self.role in MANAGER_ROLES
