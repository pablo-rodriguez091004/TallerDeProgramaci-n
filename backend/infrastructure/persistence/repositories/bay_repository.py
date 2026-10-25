from domain.catalog.entities import Bay
from domain.catalog.ports import BayRepository
from infrastructure.persistence.models.bay_model import Bay as BayRow
from infrastructure.persistence.repositories.base_repository import SqlAlchemyRepository


class SqlAlchemyBayRepository(SqlAlchemyRepository, BayRepository):
    model, entity, pk = BayRow, Bay, 'bay_id'

    def get_by_number(self, business_id, bay_number):
        return self.to_entity(BayRow.query.filter_by(business_id=business_id, bay_number=bay_number).first())

    def list_by_business(self, business_id, only_available=False):
        query = BayRow.query.filter_by(business_id=business_id)
        if only_available:
            query = query.filter_by(status='available')
        return self._to_entities(query.order_by(BayRow.bay_id))
