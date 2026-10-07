from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int | None
    name: str
    email: str
    created_at: datetime | None = None
