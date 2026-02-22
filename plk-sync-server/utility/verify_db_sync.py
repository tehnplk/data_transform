import os
import json
import re
import subprocess

def extract_description(content):
    match = re.search(r'--\s*(.*)', content)
    if match:
        return match.group(1).strip()
    match = re.search(r'/\*(.*?)\*/', content, flags=re.DOTALL)
    if match:
        return match.group(1).strip().split('\n')[0].strip()
    return ""

def clean_sql(sql):
    sql = re.sub(r'/\*.*?\*/', ' ', sql, flags=re.DOTALL)
    sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    sql = sql.replace('\n', ' ').replace('\r', ' ')
    sql = re.sub(r'\s+', ' ', sql)
    return sql.strip()

def format_key(filename):
    match = re.match(r'^(\d+)_(.*)$', filename)
    if match:
        num_part = match.group(1)
        rest_part = match.group(2)
        return f"{int(num_part):03d}_{rest_part}"
    return filename

def verify_scripts():
    base_dir = r'e:\PYTHON\data_transform\plk-sync-server\sync-scripts'
    
    # 1. Get files from disk
    disk_scripts = {}
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.sql') and not file.startswith('c_'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8-sig') as f:
                        content = f.read()
                except Exception:
                    try:
                        with open(file_path, 'r', encoding='cp874') as f:
                            content = f.read()
                    except Exception as e:
                        print(f"Error reading {file}: {e}")
                        continue
                
                cleaned_sql = clean_sql(content)
                new_key = format_key(file)
                disk_scripts[new_key] = cleaned_sql

    # 2. Get scripts from Database
    db_scripts = {}
    try:
        # Get data from c_scripts table
        process = subprocess.Popen(
            ['docker', 'exec', '-i', 'postgres', 'psql', '-U', 'admin', '-d', 'datacenter', '-t', '-A', '-c', "SELECT script_name || '|' || sql_content FROM c_scripts;"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            lines = stdout.strip().split('\n')
            for line in lines:
                if '|' in line:
                    name, sql = line.split('|', 1)
                    db_scripts[name] = sql.strip()
        else:
            print(f"Error fetching from DB: {stderr}")
            return
    except Exception as e:
        print(f"Unexpected error: {e}")
        return

    # 3. Compare
    print(f"--- Verification Report ---")
    print(f"Files on disk (sync): {len(disk_scripts)}")
    print(f"Scripts in DB table: {len(db_scripts)}")
    print("-" * 30)

    all_match = True
    
    # Check if all disk scripts are in DB and match
    for name, disk_sql in disk_scripts.items():
        if name not in db_scripts:
            print(f"[MISSING IN DB] {name}")
            all_match = False
        elif db_scripts[name] != disk_sql:
            print(f"[MISMATCH] {name}")
            # print(f"  Disk: {disk_sql[:50]}...")
            # print(f"  DB:   {db_scripts[name][:50]}...")
            all_match = False
    
    # Check for extra scripts in DB
    for name in db_scripts:
        if name not in disk_scripts:
            print(f"[EXTRA IN DB] {name}")
            all_match = False

    if all_match:
        print("✅ Success: All sync scripts match perfectly between disk and DB table.")
    else:
        print("❌ Failed: Discrepancies found.")

if __name__ == "__main__":
    verify_scripts()
