from dataclasses import dataclass
from datetime import datetime


@dataclass
class Booking:
    id: int | None
    user_id: int
    table_id: int
    booking_time: datetime
    duration_minutes: int = 60
    created_at: datetime | None = None
