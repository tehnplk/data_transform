import os
import json
import re

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
    # Regex to capture the leading number and the rest of the name
    match = re.match(r'^(\d+)_(.*)$', filename)
    if match:
        num_part = match.group(1)
        rest_part = match.group(2)
        # Pad the number part to 3 digits
        return f"{int(num_part):03d}_{rest_part}"
    return filename

def generate_sync_scripts_json():
    base_dir = r'e:\PYTHON\data_transform\plk-sync-server\sync-scripts'
    output_file = r'e:\PYTHON\data_transform\plk-sync-server\sync-scripts.json'
    
    scripts = {}
    
    # We want to maintain a list to sort them properly after renaming
    temp_scripts = []
    
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
                
                description = extract_description(content)
                cleaned_sql_content = clean_sql(content)
                
                new_key = format_key(file)
                temp_scripts.append((new_key, description, cleaned_sql_content))

    # Sort items by the new key (which is padded, so 001 comes before 010)
    temp_scripts.sort(key=lambda x: x[0])
    
    for key, desc, sql in temp_scripts:
        scripts[key] = {
            "description": desc,
            "sql": sql
        }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(scripts, f, indent=4, ensure_ascii=False)
    
    print(f"Successfully updated {output_file} with padded leading digits. Total: {len(scripts)} scripts.")

if __name__ == "__main__":
    generate_sync_scripts_json()
