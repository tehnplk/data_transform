#!/usr/bin/env python3
import psycopg2
from datetime import datetime

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5433,
    "dbname": "datacenter",
    "user": "admin",
    "password": "112233",
}

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM raw WHERE transform_datetime IS NOT NULL;")
                rows_deleted = cur.rowcount
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{now}] 888_clear_transformed: Deleted {rows_deleted} rows from raw table.")
        conn.close()
    except Exception as e:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] 888_clear_transformed Error: {e}")

if __name__ == "__main__":
    main()
