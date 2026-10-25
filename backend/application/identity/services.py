from domain.identity.entities import User
from domain.identity.ports import PasswordHasher, UserRepository
from domain.shared.errors import AuthenticationFailed, Conflict, PermissionDenied
from domain.shared.ports import UnitOfWork

PROFILE_FIELDS = ('first_name', 'middle_name', 'last_name', 'second_last_name', 'document_number', 'email', 'phone')


class AuthService:

    def __init__(self, users: UserRepository, hasher: PasswordHasher, uow: UnitOfWork):
        self._users = users
        self._hasher = hasher
        self._uow = uow

    def register(self, data, role='client'):
        """
        Registro publico (rol 'client') o cuenta creada por el dueño (rol
        'mechanic'). Correo y documento son unicos.
        """
        if self._users.get_by_email(data['email']):
            raise Conflict('Ese correo ya está registrado')
        if self._users.get_by_document(data['document_number']):
            raise Conflict('Ese número de documento ya está registrado')

        user = self._users.add(User(
            **{f: data.get(f) for f in PROFILE_FIELDS},
            role=role,
            password_hash=self._hasher.hash(data['password']),
        ))
        self._uow.commit()
        return user

    def authenticate(self, email, password):
        user = self._users.get_by_email(email)
        if not user or not self._hasher.verify(user.password_hash, password):
            raise AuthenticationFailed('Credenciales inválidas')
        if not user.is_active:
            raise PermissionDenied('Tu cuenta está inactiva')
        return user

    def get_user(self, user_id):
        return self._users.get(user_id)

    def search_clients(self, text=None):
        """Recepcion: el administrador busca al cliente antes de agendarle una cita."""
        return self._users.search_clients(text)
