from domain.catalog.entities import Part
from domain.catalog.ports import PartRepository
from infrastructure.persistence.models.part_model import Part as PartRow
from infrastructure.persistence.repositories.base_repository import SqlAlchemyRepository


class SqlAlchemyPartRepository(SqlAlchemyRepository, PartRepository):
    model, entity, pk = PartRow, Part, 'part_id'

    def list_by_business(self, business_id, include_inactive=False):
        query = PartRow.query.filter_by(business_id=business_id)
        if not include_inactive:
            query = query.filter_by(status='active')
        return self._to_entities(query.order_by(PartRow.part_id))
