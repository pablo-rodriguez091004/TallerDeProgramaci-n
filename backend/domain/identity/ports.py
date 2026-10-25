from abc import ABC, abstractmethod
from typing import Optional

from domain.identity.entities import User


class UserRepository(ABC):
    @abstractmethod
    def get(self, user_id: int) -> Optional[User]: ...

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    def get_by_document(self, document_number: str) -> Optional[User]: ...

    @abstractmethod
    def list_mechanics(self, only_active: bool = False) -> list[User]: ...

    @abstractmethod
    def add(self, user: User) -> User:
        """Agrega el usuario y devuelve la entidad con su user_id asignado."""

    @abstractmethod
    def save(self, user: User) -> None: ...


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str: ...

    @abstractmethod
    def verify(self, password_hash: str, password: str) -> bool: ...
