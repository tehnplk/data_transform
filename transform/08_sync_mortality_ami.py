#!/usr/bin/env python3
import json
from datetime import datetime, date
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values, register_default_jsonb

TABLE_NAME = "transform_sync_mortality_ami"
SOURCES = ['8_sync_mortality_ami.sql']

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5433,
    "dbname": "datacenter",
    "user": "admin",
    "password": "112233",
}

BATCH_SIZE = 5000
IGNORE_DEDUPE_COLS = {"d_update"}


def to_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in ("true", "t", "1", "yes", "y"):
        return True
    if text in ("false", "f", "0", "no", "n"):
        return False
    return None


def to_int(value):
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def to_date(value):
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except Exception:
        return None


def to_datetime(value):
    if value is None or value == "":
        return None
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


def ensure_payload(val):
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return {}
    return {}


def parse_value(value, data_type):
    if data_type in ("integer", "bigint"):
        return to_int(value)
    if data_type in ("numeric", "double precision", "real"):
        return to_float(value)
    if data_type == "boolean":
        return to_bool(value)
    if data_type == "date":
        return to_date(value)
    if data_type in ("timestamp with time zone", "timestamp without time zone"):
        return to_datetime(value)
    return value if value != "" else None


def is_newer(left, right):
    if left is None:
        return False
    if right is None:
        return True
    return left > right


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    register_default_jsonb(conn)
    with conn:
        with conn.cursor() as read_cur, conn.cursor() as write_cur:
            write_cur.execute(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position",
                (TABLE_NAME,),
            )
            columns = write_cur.fetchall()
            if not columns:
                print(f"Table not found: {TABLE_NAME}")
                return
            col_names = [c[0] for c in columns]
            col_types = {c[0]: c[1] for c in columns}
            dedupe_indexes = [idx for idx, col in enumerate(col_names) if col not in IGNORE_DEDUPE_COLS]
            d_update_idx = col_names.index("d_update") if "d_update" in col_names else None

            # Step 1: Read from raw FIRST and dedupe in memory
            all_values = []
            for source in SOURCES:
                best = {}
                read_cur.execute("SELECT hoscode, payload FROM raw WHERE source=%s AND transform_datetime IS NULL", (source,))
                while True:
                    rows = read_cur.fetchmany(BATCH_SIZE)
                    if not rows:
                        break
                    for hoscode, payload in rows:
                        payload = ensure_payload(payload)
                        row = []
                        for col in col_names:
                            if col == "hoscode":
                                val = hoscode
                            elif col == "d_update":
                                val = payload.get("d_update")
                            else:
                                val = payload.get(col)
                            val = parse_value(val, col_types[col])
                            row.append(val)
                        key = tuple(row[idx] for idx in dedupe_indexes) if dedupe_indexes else tuple(row)
                        if d_update_idx is None:
                            best.setdefault(key, row)
                            continue
                        new_dt = row[d_update_idx]
                        current = best.get(key)
                        if current is None:
                            best[key] = row
                        else:
                            cur_dt = current[d_update_idx]
                            if is_newer(new_dt, cur_dt):
                                best[key] = row
                all_values.extend(best.values())

            # Step 2: UPSERT - INSERT new data or UPDATE existing
            if all_values:
                # Get actual PK columns from database schema
                write_cur.execute("""
                    SELECT a.attname
                    FROM pg_index i
                    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                    WHERE i.indrelid = %s::regclass AND i.indisprimary
                    ORDER BY array_position(i.indkey, a.attnum)
                """, (TABLE_NAME,))
                pk_cols = [r[0] for r in write_cur.fetchall()]
                if not pk_cols:
                    pk_cols = [c for c in col_names if c != "d_update"]
                update_cols = [c for c in col_names if c not in pk_cols]

                conflict_clause = sql.SQL(", ").join(map(sql.Identifier, pk_cols))
                
                if update_cols:
                    update_set = sql.SQL(", ").join([
                        sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(c), sql.Identifier(c))
                        for c in update_cols
                    ])
                    insert_sql = sql.SQL(
                        "INSERT INTO {} ({}) VALUES %s ON CONFLICT ({}) DO UPDATE SET {}"
                    ).format(
                        sql.Identifier(TABLE_NAME),
                        sql.SQL(", ").join(map(sql.Identifier, col_names)),
                        conflict_clause,
                        update_set,
                    ).as_string(conn)
                else:
                    insert_sql = sql.SQL(
                        "INSERT INTO {} ({}) VALUES %s ON CONFLICT ({}) DO NOTHING"
                    ).format(
                        sql.Identifier(TABLE_NAME),
                        sql.SQL(", ").join(map(sql.Identifier, col_names)),
                        conflict_clause,
                    ).as_string(conn)

                execute_values(write_cur, insert_sql, all_values, page_size=1000)

                # Step 3: Stamp transform_datetime at raw
                write_cur.execute(
                    "UPDATE raw SET transform_datetime = now() "
                    "WHERE source = ANY(%s) AND transform_datetime IS NULL",
                    (SOURCES,),
                )



                print(f"{TABLE_NAME}: inserted {len(all_values)} rows from sources {SOURCES}")
            else:
                print(f"{TABLE_NAME}: no new data in raw, skipping (existing data preserved)")

    conn.close()


if __name__ == "__main__":
    main()
