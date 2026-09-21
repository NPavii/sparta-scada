"""PostgreSQL access layer for Rapid SCADA archive data."""
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from .config import get_settings


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    settings = get_settings()
    conn = psycopg.connect(settings.database_url, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()


def list_current_values() -> list[dict]:
    """Return current values for all channels."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT cnl_num, time_stamp, val, stat
                FROM mod_arc_postgre_sql.curcopy_current
                ORDER BY cnl_num
                """
            )
            return [dict(row) for row in cur.fetchall()]


def get_history(
    cnl_num: int,
    dt_from: datetime | None = None,
    dt_to: datetime | None = None,
    limit: int = 1000,
) -> list[dict]:
    """Return historical values for a channel, newest first."""
    query = """
        SELECT cnl_num, time_stamp, val, stat
        FROM mod_arc_postgre_sql.mincopy_historical
        WHERE cnl_num = %s
    """
    params: list = [cnl_num]
    if dt_from is not None:
        query += " AND time_stamp >= %s"
        params.append(dt_from)
    if dt_to is not None:
        query += " AND time_stamp <= %s"
        params.append(dt_to)
    query += " ORDER BY time_stamp DESC LIMIT %s"
    params.append(limit)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = [dict(row) for row in cur.fetchall()]
    return rows


def get_latest_timestamp(cnl_num: int) -> datetime | None:
    """Return the most recent timestamp for a channel."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT MAX(time_stamp) AS ts
                FROM mod_arc_postgre_sql.mincopy_historical
                WHERE cnl_num = %s
                """,
                (cnl_num,),
            )
            row = cur.fetchone()
            return row["ts"] if row and row["ts"] else None


def check_connection() -> bool:
    """Return True if the database is reachable."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True
    except psycopg.Error:
        return False
