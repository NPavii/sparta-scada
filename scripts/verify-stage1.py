#!/usr/bin/env python3
"""Verify Stage 1: OPC UA tags flow through Rapid SCADA into PostgreSQL."""
import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv()

raw_host = os.getenv("POSTGRES_HOST", "localhost")
DB_HOST = "localhost" if raw_host in ("sparta-postgres", "postgres", "host.docker.internal") else raw_host
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "scada")
DB_USER = os.getenv("POSTGRES_USER", "scada")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "scada")

EXPECTED_CHANNELS = {101, 102, 103, 104, 105, 106}


def main():
    conn_str = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASS}"
    try:
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()

        cur.execute("SELECT count(*) FROM mod_arc_postgre_sql.curcopy_current")
        current_count = cur.fetchone()[0]
        print(f"Current data rows: {current_count}")

        cur.execute("SELECT cnl_num FROM mod_arc_postgre_sql.curcopy_current")
        found_channels = {row[0] for row in cur.fetchall()}
        missing = EXPECTED_CHANNELS - found_channels
        if missing:
            print(f"Missing channels in current data: {missing}")
            return 1

        cur.execute(
            "SELECT count(*) FROM mod_arc_postgre_sql.mincopy_historical "
            "WHERE time_stamp >= now() - interval '5 minutes'"
        )
        recent_historical = cur.fetchone()[0]
        print(f"Historical rows in last 5 minutes: {recent_historical}")

        if recent_historical == 0:
            print("No recent historical data found")
            return 1

        cur.execute(
            "SELECT cnl_num, time_stamp, val, stat FROM mod_arc_postgre_sql.curcopy_current "
            "ORDER BY cnl_num"
        )
        print("\nCurrent values:")
        for row in cur.fetchall():
            print(f"  Cnl {row[0]}: {row[2]} at {row[1]} (stat {row[3]})")

        print("\nStage 1 verification passed: OPC UA data is flowing into PostgreSQL.")
        return 0
    except Exception as e:
        print(f"Verification failed: {e}")
        return 1
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
