from domain.tracking.entities import PartUsage, TrackingRecord
from domain.tracking.ports import TrackingRepository
from infrastructure.persistence.extensions import db
from infrastructure.persistence.models.service_tracking_model import ServiceTracking as TrackingRow
from infrastructure.persistence.models.service_tracking_parts_model import ServiceTrackingPart as UsageRow


def _to_record(row):
    return TrackingRecord(
        tracking_id=row.tracking_id, appointment_id=row.appointment_id, status=row.status, notes=row.notes,
        current_mileage=row.current_mileage, recorded_at=row.recorded_at,
        parts_used=[PartUsage(part_id=u.part_id, part_name=u.part.part_name, quantity=u.quantity)
                    for u in row.parts_used],
    )


class SqlAlchemyTrackingRepository(TrackingRepository):

    def list_by_appointment(self, appointment_id):
        rows = TrackingRow.query.filter_by(appointment_id=appointment_id).order_by(TrackingRow.recorded_at)
        return [_to_record(row) for row in rows]

    def add(self, record):
        row = TrackingRow(appointment_id=record.appointment_id, status=record.status, notes=record.notes,
                          current_mileage=record.current_mileage)
        db.session.add(row)
        db.session.flush()
        for usage in record.parts_used:
            db.session.add(UsageRow(tracking_id=row.tracking_id, part_id=usage.part_id, quantity=usage.quantity))
        db.session.flush()
        record.tracking_id, record.recorded_at = row.tracking_id, row.recorded_at
        return record
