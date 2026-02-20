import os
import re
import glob
import shutil

TRANSFORM_DIR = "/home/adminplk/transform"

OLD_PK_LINE = '                pk_cols = [c for c in col_names if c != "d_update"]'

NEW_PK_BLOCK = '''                # Get actual PK columns from database schema
                write_cur.execute("""
                    SELECT a.attname
                    FROM pg_index i
                    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                    WHERE i.indrelid = %s::regclass AND i.indisprimary
                    ORDER BY array_position(i.indkey, a.attnum)
                """, (TABLE_NAME,))
                pk_cols = [r[0] for r in write_cur.fetchall()]
                if not pk_cols:
                    pk_cols = [c for c in col_names if c != "d_update"]'''

def patch_file(filepath):
    fname = os.path.basename(filepath)
    with open(filepath, "r") as f:
        content = f.read()

    if OLD_PK_LINE not in content:
        print(f"  SKIP {fname}: pattern not found")
        return False

    content = content.replace(OLD_PK_LINE, NEW_PK_BLOCK)
    
    bak = filepath + ".bak3"
    shutil.copy2(filepath, bak)
    with open(filepath, "w") as f:
        f.write(content)
    print(f"  PATCHED {fname} (backup: {bak})")
    return True

def main():
    files = sorted(glob.glob(os.path.join(TRANSFORM_DIR, "*.py")))
    patched = 0
    for fpath in files:
        fname = os.path.basename(fpath)
        if not fname[0].isdigit():
            continue
        if ".bak" in fname:
            continue
        print(f"--- {fname} ---")
        if patch_file(fpath):
            patched += 1
    print(f"\n=== Patched {patched} files ===")

if __name__ == "__main__":
    main()
