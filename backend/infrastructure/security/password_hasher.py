from werkzeug.security import check_password_hash, generate_password_hash

from domain.identity.ports import PasswordHasher


class WerkzeugPasswordHasher(PasswordHasher):
    def hash(self, password):
        return generate_password_hash(password)

    def verify(self, password_hash, password):
        return check_password_hash(password_hash, password)
