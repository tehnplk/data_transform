import psycopg2

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5433,
    "dbname": "datacenter",
    "user": "admin",
    "password": "112233",
}

def main():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get all sync tables
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'sync_%' ORDER BY tablename;")
        tables = [r[0] for r in cur.fetchall()]
        
        print(f"{'Table Name':<35} {'Hoscode':<10} {'Count':<10}")
        print("-" * 55)
        
        for table in tables:
            # Check if hoscode exists
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'hoscode';")
            if not cur.fetchone():
                continue
                
            cur.execute(f"SELECT hoscode, COUNT(*) FROM {table} GROUP BY hoscode ORDER BY hoscode;")
            rows = cur.fetchall()
            
            if rows:
                for r in rows:
                    print(f"{table:<35} {r[0]:<10} {r[1]:<10}")
            else:
                # print(f"{table:<35} {'-':<10} {'0':<10}") # Uncomment to see empty tables
                pass
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    main()
