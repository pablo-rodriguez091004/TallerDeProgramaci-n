from domain.catalog.entities import Business
from domain.catalog.ports import BusinessRepository
from infrastructure.persistence.models.business_model import Business as BusinessRow
from infrastructure.persistence.repositories.base_repository import SqlAlchemyRepository


class SqlAlchemyBusinessRepository(SqlAlchemyRepository, BusinessRepository):
    model, entity, pk = BusinessRow, Business, 'business_id'

    def get_by_owner(self, owner_user_id):
        return self.to_entity(BusinessRow.query.filter_by(owner_user_id=owner_user_id).first())

    def first(self):
        return self.to_entity(BusinessRow.query.order_by(BusinessRow.business_id).first())
