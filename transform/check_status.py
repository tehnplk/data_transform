import os
import glob
import re
import psycopg2
from collections import defaultdict

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5433,
    "dbname": "datacenter",
    "user": "admin",
    "password": "112233",
}

TRANSFORM_DIR = "/home/adminplk/transform"

def get_mappings():
    mappings = []
    files = glob.glob(os.path.join(TRANSFORM_DIR, "*.py"))
    for fpath in sorted(files):
        fname = os.path.basename(fpath)
        if not fname[0].isdigit(): continue 

        with open(fpath, "r") as f:
            content = f.read()
            
        m_table = re.search(r'TABLE_NAME\s*=\s*"([^"]+)"', content)
        if not m_table: continue
        table_name = m_table.group(1)
        
        # Simple regex to get content inside SOURCES = [...]
        m_sources = re.search(r"SOURCES\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if m_sources:
            inner = m_sources.group(1)
            # Find all strings inside quotes
            sources = re.findall(r"['\"]([^'\"]+)['\"]", inner)
            for s in sources:
                mappings.append((s, table_name))
            
    return mappings

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        mappings = get_mappings()
        
        # Header
        print(f"{'Source':<32} | {'Raw (Pending)':<15} | {'Target Table':<30} | {'Transformed Data (by Hoscode)'}")
        print("-" * 125)

        # 1. Get Raw Data Counts
        cur.execute("SELECT source, hoscode, COUNT(*) FROM raw GROUP BY source, hoscode")
        raw_data = defaultdict(lambda: defaultdict(int))
        for r in cur.fetchall():
            raw_data[r[0]][r[1]] = r[2]

        # 2. Iterate Mappings
        for source, table_name in mappings:
            # Get Target Data Counts
            target_str = ""
            try:
                # Check hoscode column
                cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' AND column_name = 'hoscode'")
                if cur.fetchone():
                    cur.execute(f"SELECT hoscode, COUNT(*) FROM {table_name} GROUP BY hoscode ORDER BY hoscode")
                    rows = cur.fetchall()
                    if rows:
                        parts = [f"{r[0]}: {r[1]:,}" for r in rows] # 11251: 1,000
                        target_str = " | ".join(parts)
                    else:
                        target_str = "0"
                else:
                    target_str = "N/A (No hoscode)"
            except Exception as e:
                target_str = f"Error: {e}"

            # Raw Pending String
            raw_str = ""
            if source in raw_data:
                parts = [f"{h}: {c}" for h, c in raw_data[source].items()]
                raw_str = ", ".join(parts)
            else:
                raw_str = "-"

            print(f"{source:<32} | {raw_str:<15} | {table_name:<30} | {target_str}")

    except Exception as e:
        print(e)
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    main()
