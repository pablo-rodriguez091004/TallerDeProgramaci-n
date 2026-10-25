from domain.identity.entities import User
from domain.identity.ports import UserRepository
from infrastructure.persistence.models.user_model import User as UserRow
from infrastructure.persistence.repositories.base_repository import SqlAlchemyRepository


class SqlAlchemyUserRepository(SqlAlchemyRepository, UserRepository):
    model, entity, pk = UserRow, User, 'user_id'

    def get_by_email(self, email):
        return self.to_entity(UserRow.query.filter_by(email=email).first())

    def get_by_document(self, document_number):
        return self.to_entity(UserRow.query.filter_by(document_number=document_number).first())

    def list_mechanics(self, only_active=False):
        query = UserRow.query.filter_by(role='mechanic')
        if only_active:
            query = query.filter_by(status='active')
        return self._to_entities(query.order_by(UserRow.user_id))
