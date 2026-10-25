from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

TRACKING_STATUSES = ('received', 'diagnosing', 'in_repair', 'quality_check', 'ready_for_pickup', 'delivered')


@dataclass(kw_only=True)
class PartUsage:
    part_id: int
    quantity: int
    part_name: Optional[str] = None


@dataclass(kw_only=True)
class TrackingRecord:
    tracking_id: Optional[int] = None
    appointment_id: int
    status: str
    notes: Optional[str] = None
    current_mileage: Optional[int] = None
    recorded_at: Optional[datetime] = None
    parts_used: list[PartUsage] = field(default_factory=list)
