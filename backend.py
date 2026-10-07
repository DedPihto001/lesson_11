"""Booking application data access and demonstration entry point."""

from datetime import datetime, timedelta
from typing import Any

from postgres_driver import get_cursor


def init_db() -> None:
    """Create the application's tables if they do not already exist."""
    statements = (
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tables (
            id SERIAL PRIMARY KEY,
            number INT UNIQUE NOT NULL,
            seats INT NOT NULL CHECK (seats > 0),
            description TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            table_id INT NOT NULL REFERENCES tables(id) ON DELETE CASCADE,
            booking_time TIMESTAMP NOT NULL,
            duration_minutes INT NOT NULL DEFAULT 60
                CHECK (duration_minutes > 0),
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
    )
    with get_cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


def _validate_duration(duration_minutes: int) -> None:
    if duration_minutes <= 0:
        raise ValueError("duration_minutes must be greater than zero")


def create_user(name: str, email: str) -> int:
    with get_cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id",
            (name, email),
        )
        return int(cursor.fetchone()["id"])


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone()


def get_all_users() -> list[dict[str, Any]]:
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM users ORDER BY id")
        return list(cursor.fetchall())


def update_user(user_id: int, name: str, email: str) -> bool:
    with get_cursor() as cursor:
        cursor.execute(
            "UPDATE users SET name = %s, email = %s WHERE id = %s",
            (name, email, user_id),
        )
        return cursor.rowcount > 0


def delete_user(user_id: int) -> bool:
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        return cursor.rowcount > 0


def create_table(number: int, seats: int, description: str | None = None) -> int:
    if seats <= 0:
        raise ValueError("seats must be greater than zero")
    with get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO tables (number, seats, description)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (number, seats, description),
        )
        return int(cursor.fetchone()["id"])


def get_table_by_id(table_id: int) -> dict[str, Any] | None:
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM tables WHERE id = %s", (table_id,))
        return cursor.fetchone()


def get_all_tables() -> list[dict[str, Any]]:
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM tables ORDER BY number")
        return list(cursor.fetchall())


def update_table(
    table_id: int,
    number: int,
    seats: int,
    description: str | None = None,
) -> bool:
    if seats <= 0:
        raise ValueError("seats must be greater than zero")
    with get_cursor() as cursor:
        cursor.execute(
            """
            UPDATE tables
            SET number = %s, seats = %s, description = %s
            WHERE id = %s
            """,
            (number, seats, description, table_id),
        )
        return cursor.rowcount > 0


def delete_table(table_id: int) -> bool:
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM tables WHERE id = %s", (table_id,))
        return cursor.rowcount > 0


def check_table_availability(
    table_id: int,
    booking_time: datetime,
    duration_minutes: int = 60,
) -> bool:
    _validate_duration(duration_minutes)
    with get_cursor() as cursor:
        cursor.execute("SELECT id FROM tables WHERE id = %s", (table_id,))
        if cursor.fetchone() is None:
            raise ValueError(f"Table {table_id} does not exist")
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM bookings
                WHERE table_id = %s
                  AND %s < booking_time
                      + duration_minutes * INTERVAL '1 minute'
                  AND %s + %s * INTERVAL '1 minute' > booking_time
            ) AS is_booked
            """,
            (table_id, booking_time, booking_time, duration_minutes),
        )
        return not bool(cursor.fetchone()["is_booked"])


def create_booking(
    user_id: int,
    table_id: int,
    booking_time: datetime,
    duration_minutes: int = 60,
) -> int:
    _validate_duration(duration_minutes)
    with get_cursor() as cursor:
        # Locking the table row serializes concurrent booking attempts for it.
        cursor.execute("SELECT id FROM tables WHERE id = %s FOR UPDATE", (table_id,))
        if cursor.fetchone() is None:
            raise ValueError(f"Table {table_id} does not exist")
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM bookings
                WHERE table_id = %s
                  AND %s < booking_time
                      + duration_minutes * INTERVAL '1 minute'
                  AND %s + %s * INTERVAL '1 minute' > booking_time
            ) AS is_booked
            """,
            (table_id, booking_time, booking_time, duration_minutes),
        )
        if cursor.fetchone()["is_booked"]:
            raise ValueError("The selected table is already booked for this time")
        cursor.execute(
            """
            INSERT INTO bookings
                (user_id, table_id, booking_time, duration_minutes)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (user_id, table_id, booking_time, duration_minutes),
        )
        return int(cursor.fetchone()["id"])


def get_booking_by_id(booking_id: int) -> dict[str, Any] | None:
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT b.*, u.name AS user_name, u.email AS user_email,
                   t.number AS table_number
            FROM bookings AS b
            JOIN users AS u ON u.id = b.user_id
            JOIN tables AS t ON t.id = b.table_id
            WHERE b.id = %s
            """,
            (booking_id,),
        )
        return cursor.fetchone()


def get_all_bookings() -> list[dict[str, Any]]:
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT b.id, b.user_id, u.name AS user_name, u.email AS user_email,
                   b.table_id, t.number AS table_number, b.booking_time,
                   b.duration_minutes, b.created_at
            FROM bookings AS b
            JOIN users AS u ON u.id = b.user_id
            JOIN tables AS t ON t.id = b.table_id
            ORDER BY b.booking_time, b.id
            """
        )
        return list(cursor.fetchall())


def update_booking(
    booking_id: int,
    user_id: int,
    table_id: int,
    booking_time: datetime,
    duration_minutes: int = 60,
) -> bool:
    _validate_duration(duration_minutes)
    with get_cursor() as cursor:
        cursor.execute(
            "SELECT id FROM tables WHERE id = %s FOR UPDATE",
            (table_id,),
        )
        if cursor.fetchone() is None:
            raise ValueError(f"Table {table_id} does not exist")
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM bookings
                WHERE table_id = %s AND id <> %s
                  AND %s < booking_time
                      + duration_minutes * INTERVAL '1 minute'
                  AND %s + %s * INTERVAL '1 minute' > booking_time
            ) AS is_booked
            """,
            (table_id, booking_id, booking_time, booking_time, duration_minutes),
        )
        if cursor.fetchone()["is_booked"]:
            raise ValueError("The selected table is already booked for this time")
        cursor.execute(
            """
            UPDATE bookings
            SET user_id = %s, table_id = %s, booking_time = %s,
                duration_minutes = %s
            WHERE id = %s
            """,
            (user_id, table_id, booking_time, duration_minutes, booking_id),
        )
        return cursor.rowcount > 0


def delete_booking(booking_id: int) -> bool:
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
        return cursor.rowcount > 0


def seed_demo_data() -> None:
    """Create at least three example users, tables, and two bookings."""
    users = (
        ("Anna Ivanova", "anna@example.com"),
        ("Ivan Petrov", "ivan@example.com"),
        ("Maria Sidorova", "maria@example.com"),
    )
    tables = (
        (1, 2, "Window seat"),
        (2, 4, "Family table"),
        (3, 6, "Large group"),
    )

    user_ids: list[int] = []
    for name, email in users:
        with get_cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing = cursor.fetchone()
        user_ids.append(
            int(existing["id"]) if existing else create_user(name, email)
        )

    table_ids: list[int] = []
    for number, seats, description in tables:
        with get_cursor() as cursor:
            cursor.execute("SELECT id FROM tables WHERE number = %s", (number,))
            existing = cursor.fetchone()
        table_ids.append(
            int(existing["id"])
            if existing
            else create_table(number, seats, description)
        )

    start = (datetime.now() + timedelta(days=1)).replace(second=0, microsecond=0)
    create_booking(user_ids[0], table_ids[0], start, 60)
    create_booking(user_ids[1], table_ids[1], start + timedelta(hours=1), 90)


def main() -> None:
    init_db()
    seed_demo_data()
    print("Bookings:")
    for booking in get_all_bookings():
        print(dict(booking))
    print(
        """
PgAdmin verification queries:
SELECT * FROM users ORDER BY id;
SELECT * FROM tables ORDER BY number;
SELECT * FROM bookings ORDER BY booking_time;
SELECT b.id, u.name, t.number, b.booking_time, b.duration_minutes
FROM bookings AS b
JOIN users AS u ON u.id = b.user_id
JOIN tables AS t ON t.id = b.table_id
ORDER BY b.booking_time;
"""
    )


if __name__ == "__main__":
    main()
