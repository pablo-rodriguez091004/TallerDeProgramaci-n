"""
Base de los adaptadores de persistencia: traduce filas ORM <-> entidades.

Las entidades del dominio son dataclasses con los mismos nombres de campo
que las columnas, asi el mapeo es generico. Los repositorios agregan
cambios a la sesion (add + flush) pero NO hacen commit: eso lo decide el
caso de uso a traves del puerto UnitOfWork.
"""

from dataclasses import fields

from infrastructure.persistence.extensions import db


class SqlAlchemyRepository:
    model = None   # clase ORM
    entity = None  # dataclass del dominio
    pk = None      # nombre de la clave primaria

    def _fields(self):
        return [f.name for f in fields(self.entity) if hasattr(self.model, f.name)]

    def to_entity(self, row):
        if row is None:
            return None
        return self.entity(**{name: getattr(row, name) for name in self._fields()})

    def _to_entities(self, rows):
        return [self.to_entity(row) for row in rows]

    def _row(self, entity_id):
        return db.session.get(self.model, entity_id)

    def get(self, entity_id):
        return self.to_entity(self._row(entity_id))

    def add(self, entity):
        values = {name: getattr(entity, name) for name in self._fields()}
        if values.get(self.pk) is None:
            values.pop(self.pk, None)
        # Columnas con default en la BD (created_at, ...): si la entidad trae
        # None se omiten para que el default aplique.
        values = {k: v for k, v in values.items() if v is not None or k not in self._server_defaults()}
        row = self.model(**values)
        db.session.add(row)
        db.session.flush()  # asigna el id sin cerrar la transaccion
        return self.to_entity(row)

    def save(self, entity):
        row = self._row(getattr(entity, self.pk))
        for name in self._fields():
            if name != self.pk:
                setattr(row, name, getattr(entity, name))
        db.session.flush()

    def delete(self, entity_id):
        db.session.delete(self._row(entity_id))
        db.session.flush()

    def _server_defaults(self):
        columns = self.model.__table__.columns
        return {c.name for c in columns if c.default is not None or c.server_default is not None}
