import os
import re

directory = r'e:\PYTHON\data_transform\transform'

for filename in os.listdir(directory):
    if filename.endswith('.py') and re.match(r'^\d+_sync_.*\.py$', filename):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Update Step 1: Find actual sources dynamically
        old_step1_pattern = r'# Step 1: Read from raw FIRST and dedupe in memory\s+all_values = \[\]\s+for source in SOURCES:'
        new_step1 = """# Step 1: Read from raw FIRST and dedupe in memory
            all_values = []
            
            # Find all sources that match the base name (ignoring prefix digits)
            base_names = [s.split('_', 1)[-1] if '_' in s else s for s in SOURCES]
            read_cur.execute(
                "SELECT DISTINCT source FROM raw "
                "WHERE (source = ANY(%s) OR source LIKE ANY(%s)) "
                "AND transform_datetime IS NULL",
                (base_names, [f'%_{bn}' for bn in base_names])
            )
            actual_sources = [r[0] for r in read_cur.fetchall()]
            
            for source in actual_sources:"""
        
        content = re.sub(old_step1_pattern, new_step1, content)

        # 2. Update Step 3: Use actual_sources for update
        old_step3_pattern = r'# Step 3: Stamp transform_datetime at raw\s+write_cur\.execute\(\s+"UPDATE raw SET transform_datetime = now\(\) "\s+"WHERE source = ANY\(%s\) AND transform_datetime IS NULL",\s+\(SOURCES,\),\s+\)'
        new_step3 = """# Step 3: Stamp transform_datetime at raw
                write_cur.execute(
                    "UPDATE raw SET transform_datetime = now() "
                    "WHERE source = ANY(%s) AND transform_datetime IS NULL",
                    (actual_sources,),
                )"""
        
        content = re.sub(old_step3_pattern, new_step3, content)

        # 3. Update the final print statement
        old_print_pattern = r'print\(f"{TABLE_NAME}: inserted {len\(all_values\)} rows from sources {SOURCES}"\)'
        new_print = 'print(f"{TABLE_NAME}: inserted {len(all_values)} rows from sources {actual_sources}")'
        
        content = re.sub(old_print_pattern, new_print, content)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filename}")
