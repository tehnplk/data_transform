import os
import glob
import shutil

TRANSFORM_DIR = "/home/adminplk/transform"

def patch_file(filepath):
    fname = os.path.basename(filepath)
    
    with open(filepath, "r") as f:
        content = f.read()

    original = content

    # 1. Update SELECT query
    old_select = 'read_cur.execute("SELECT hoscode, payload FROM raw WHERE source=%s", (source,))'
    new_select = 'read_cur.execute("SELECT hoscode, payload FROM raw WHERE source=%s AND transform_datetime IS NULL", (source,))'
    
    if old_select in content:
        content = content.replace(old_select, new_select)
        print(f"  Patched SELECT query in {fname}")
    elif new_select in content:
        print(f"  SELECT query already patched in {fname}")
    else:
        print(f"  WARNING: Could not find old SELECT query in {fname}")

    # 2. Remove DELETE query
    old_delete = '''                # Step 4: Delete processed rows from raw
                write_cur.execute(
                    "DELETE FROM raw WHERE source = ANY(%s) AND transform_datetime IS NOT NULL",
                    (SOURCES,),
                )'''
    
    # Also handle string variations
    old_delete_2 = '''                # Step 4: Delete processed rows from raw
                write_cur.execute(
                    "DELETE FROM raw WHERE source = ANY(%s)",
                    (SOURCES,),
                )'''

    if old_delete in content:
        content = content.replace(old_delete, "")
        print(f"  Removed DELETE query in {fname}")
    elif old_delete_2 in content:
        content = content.replace(old_delete_2, "")
        print(f"  Removed DELETE query in {fname}")
    else:
        print(f"  WARNING: Could not find old DELETE query in {fname}")

    if content != original:
        bak = filepath + ".bak_nodelete"
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
        if fname.endswith(".bak") or ".bak" in fname:
            continue
        print(f"\n--- {fname} ---")
        if patch_file(fpath):
            patched += 1

    print(f"\n=== Patched {patched} files ===")

if __name__ == "__main__":
    main()
