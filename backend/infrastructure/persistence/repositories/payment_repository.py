from domain.payments.entities import Payment
from domain.payments.ports import PaymentRepository
from infrastructure.persistence.models.payment_model import Payment as PaymentRow
from infrastructure.persistence.repositories.base_repository import SqlAlchemyRepository


class SqlAlchemyPaymentRepository(SqlAlchemyRepository, PaymentRepository):
    model, entity, pk = PaymentRow, Payment, 'payment_id'

    def list_by_appointment(self, appointment_id):
        return self._to_entities(PaymentRow.query.filter_by(appointment_id=appointment_id).order_by(PaymentRow.payment_id))
