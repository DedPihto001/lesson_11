"""Context-managed PostgreSQL connections and dictionary cursors."""

from contextlib import contextmanager
import os
from typing import Generator

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor


load_dotenv()


def _connection_settings() -> dict[str, str]:
    required = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError(
            "Missing database settings in .env: " + ", ".join(missing)
        )
    return {
        "host": os.environ["DB_HOST"],
        "port": os.environ["DB_PORT"],
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }


@contextmanager
def get_connection() -> Generator[connection, None, None]:
    """Open a connection, commit on success, roll back on error, and close it."""
    conn = psycopg2.connect(**_connection_settings())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_cursor() -> Generator[RealDictCursor, None, None]:
    """Yield a RealDictCursor whose connection is safely finalized."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            yield cursor
