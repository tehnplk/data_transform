import psycopg2

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5433,
    "dbname": "datacenter",
    "user": "admin",
    "password": "112233",
}

def get_default_for_type(dtype):
    dtype = dtype.lower()
    if "character" in dtype or dtype == "text":
        return "''"
    elif "integer" in dtype or "smallint" in dtype or "bigint" in dtype:
        return "0"
    elif "numeric" in dtype or "double" in dtype or "real" in dtype or "decimal" in dtype:
        return "0"
    elif "date" == dtype:
        return "'1900-01-01'"
    elif "timestamp" in dtype:
        return "'1900-01-01 00:00:00'"
    elif "boolean" in dtype:
        return "false"
    else:
        return "''"

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    cur.execute("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname='public' AND tablename LIKE 'sync_%' 
        AND tablename NOT LIKE 'transform_sync_%'
        ORDER BY tablename;
    """)
    tables = [r[0] for r in cur.fetchall()]
    print(f"Found {len(tables)} sync tables to migrate\n")

    for old_name in tables:
        new_name = "transform_" + old_name
        print(f"=== {old_name} -> {new_name} ===")

        cur.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position",
            (old_name,)
        )
        all_cols_info = cur.fetchall()
        pk_cols = [(c, dt) for c, dt in all_cols_info if c != "d_update"]

        # Step A: Fix NULLs + NOT NULL
        for col, dtype in pk_cols:
            default_val = get_default_for_type(dtype)
            cur.execute(f'UPDATE "{old_name}" SET "{col}" = {default_val} WHERE "{col}" IS NULL;')
            updated = cur.rowcount
            if updated > 0:
                print(f"  Fixed {updated} NULLs in {col}")
            cur.execute(f'ALTER TABLE "{old_name}" ALTER COLUMN "{col}" SET NOT NULL;')

        # Step B: Remove exact duplicates
        pk_col_list = ", ".join([f'"{c}"' for c, _ in pk_cols])
        and_clause = " AND ".join([f'a."{c}" = b."{c}"' for c, _ in pk_cols])
        cur.execute(f'DELETE FROM "{old_name}" a USING "{old_name}" b WHERE a.ctid < b.ctid AND {and_clause};')
        deleted = cur.rowcount
        if deleted > 0:
            print(f"  Removed {deleted} duplicate rows")

        # Step C: Rename table
        cur.execute(f'ALTER TABLE "{old_name}" RENAME TO "{new_name}";')
        print(f"  Renamed -> {new_name}")

        # Step D: Add composite PK
        pk_name = f"pk_{new_name}"
        cur.execute(f'ALTER TABLE "{new_name}" ADD CONSTRAINT "{pk_name}" PRIMARY KEY ({pk_col_list});')
        print(f"  PK added: ({pk_col_list})")
        print()

    conn.commit()
    print("=== All done! Migration committed. ===")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
