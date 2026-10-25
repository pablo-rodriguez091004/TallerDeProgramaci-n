from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from domain.shared.errors import PersistenceConflict
from domain.shared.ports import Clock, UnitOfWork
from infrastructure.persistence.extensions import db


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Usa la sesion de Flask-SQLAlchemy (una por request)."""

    def commit(self):
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise PersistenceConflict('The change violates a database constraint') from exc

    def rollback(self):
        db.session.rollback()


class SystemClock(Clock):
    def now(self):
        # Hora UTC sin zona, el mismo formato que guardaba datetime.utcnow().
        return datetime.now(timezone.utc).replace(tzinfo=None)
