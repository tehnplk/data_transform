import os
import re
import glob
import shutil

TRANSFORM_DIR = "/home/adminplk/transform"

def patch_file(filepath):
    fname = os.path.basename(filepath)
    
    with open(filepath, "r") as f:
        content = f.read()

    original = content

    # 1. Change TABLE_NAME from "sync_*" to "transform_sync_*"
    m = re.search(r'TABLE_NAME\s*=\s*"(sync_[^"]+)"', content)
    if not m:
        print(f"  SKIP {fname}: no TABLE_NAME found")
        return False
    
    old_table = m.group(1)
    new_table = "transform_" + old_table
    content = content.replace(f'TABLE_NAME = "{old_table}"', f'TABLE_NAME = "{new_table}"')
    print(f"  TABLE_NAME: {old_table} -> {new_table}")

    # 2. Replace TRUNCATE + INSERT logic with UPSERT logic
    # Find and replace the "Step 2" block
    
    # Old pattern: TRUNCATE TABLE + INSERT INTO + execute_values
    old_step2 = '''            # Step 2: Only TRUNCATE + INSERT if there is new data
            if all_values:
                write_cur.execute(sql.SQL("TRUNCATE TABLE {}").format(sql.Identifier(TABLE_NAME)))

                insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES %s").format(
                    sql.Identifier(TABLE_NAME),
                    sql.SQL(", ").join(map(sql.Identifier, col_names)),
                ).as_string(conn)

                execute_values(write_cur, insert_sql, all_values, page_size=1000)'''

    new_step2 = '''            # Step 2: UPSERT - INSERT new data or UPDATE existing
            if all_values:
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

                execute_values(write_cur, insert_sql, all_values, page_size=1000)'''

    if old_step2 in content:
        content = content.replace(old_step2, new_step2)
        print(f"  Replaced TRUNCATE+INSERT -> UPSERT")
    else:
        print(f"  WARNING: Could not find exact TRUNCATE pattern in {fname}")
        return False

    if content != original:
        # Backup
        bak = filepath + ".bak2"
        shutil.copy2(filepath, bak)
        with open(filepath, "w") as f:
            f.write(content)
        print(f"  Saved! (backup: {bak})")
        return True
    return False

def main():
    files = sorted(glob.glob(os.path.join(TRANSFORM_DIR, "*.py")))
    patched = 0
    for fpath in files:
        fname = os.path.basename(fpath)
        if not fname[0].isdigit():
            continue
        if fname.endswith(".bak") or fname.endswith(".bak2"):
            continue
        print(f"\n--- {fname} ---")
        if patch_file(fpath):
            patched += 1

    print(f"\n=== Patched {patched} files ===")

if __name__ == "__main__":
    main()
