from dataclasses import dataclass


@dataclass
class Table:
    id: int | None
    number: int
    seats: int
    description: str | None = None
