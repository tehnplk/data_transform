import psycopg2
import subprocess
import os
import datetime

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5433,
    "dbname": "datacenter",
    "user": "admin",
    "password": "112233",
}
TRANSFORM_DIR = "/home/adminplk/transform"
LOG_DIR = os.path.join(TRANSFORM_DIR, "logs")

# Mapping: source name in raw table -> Python script filename
SOURCE_TO_SCRIPT = {
    "0_sync_test.sql": "00_sync_test.py",
    "1_sync_bed_an_occupancy.sql": "01_sync_bed_an_occupancy.py",
    "2_sync_bed_type_all.sql": "02_sync_bed_type_all.py",
    "3_sync_critical_wait_bed.sql": "03_sync_critical_wait_bed.py",
    "4_sync_drgs_rw_top10.sql": "04_sync_drgs_rw_top10.py",
    "5_sync_drgs_sum.sql": "05_sync_drgs_sum.py",
    "6_sync_icu_semi_icu_case_realtime.sql": "06_sync_icu_semi_icu_case_realtime.py",
    "8_sync_mortality_ami.sql": "08_sync_mortality_ami.py",
    "9_sync_mortality_sepsis.sql": "09_sync_mortality_sepsis.py",
    "10_sync_normal_ward_death.sql": "10_sync_normal_ward_death.py",
    "11_sync_or_utilization_rate.sql": "11_sync_or_utilization_rate.py",
    "12_sync_refer_paperless.sql": "12_sync_refer_paperless.py",
    "13_sync_refer_top10.sql": "13_sync_refer_top10.py",
    "14_sync_waiting_time_cataract.sql": "14_sync_waiting_time_cataract.py",
    "15_sync_waiting_time_hernia.sql": "15_sync_waiting_time_hernia.py",
}

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.date.today().strftime("%Y%m%d")
    log_file = os.path.join(LOG_DIR, f"dispatcher_{today}.log")
    os.makedirs(LOG_DIR, exist_ok=True)
    line = f"[{timestamp}] {message}"
    with open(log_file, "a") as f:
        f.write(line + "\n")
    print(line)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Find sources with pending (untransformed) data
        cur.execute("SELECT DISTINCT source FROM raw WHERE transform_datetime IS NULL")
        pending_sources = [r[0] for r in cur.fetchall()]

        if not pending_sources:
            log("No pending data in raw table. Nothing to do.")
            cur.close()
            conn.close()
            return

        log(f"Found pending data for {len(pending_sources)} source(s): {pending_sources}")
        executed_list = []
        executed_count = 0
        skipped = 0

        for source in sorted(pending_sources):
            script = SOURCE_TO_SCRIPT.get(source)
            if not script:
                log(f"  SKIP: No script mapping for source '{source}'")
                skipped += 1
                continue

            script_path = os.path.join(TRANSFORM_DIR, script)
            if not os.path.exists(script_path):
                log(f"  SKIP: Script file not found: {script_path}")
                skipped += 1
                continue

            log(f"  RUN: {script} (source: {source})")
            try:
                today = datetime.date.today().strftime("%Y%m%d")
                log_file = os.path.join(LOG_DIR, f"dispatcher_{today}.log")
                with open(log_file, "a") as f:
                    f.write(f"--- Output of {script} ---\n")
                    f.flush()
                    result = subprocess.run(
                        ["python3", script_path],
                        cwd=TRANSFORM_DIR,
                        stdout=f,
                        stderr=f,
                        text=True,
                    )
                    f.write(f"--- End of {script} (exit={result.returncode}) ---\n")

                if result.returncode == 0:
                    log(f"  OK: {script} completed successfully")
                    executed_count += 1
                    executed_list.append(script)
                else:
                    log(f"  ERROR: {script} exited with code {result.returncode}")
            except Exception as e:
                log(f"  EXCEPTION running {script}: {e}")

        summary = f"Summary: {executed_count} executed, {skipped} skipped, {len(pending_sources)} total sources"
        log(summary)

        # Log to Database if something was executed
        if executed_count > 0:
            try:
                note = f"Transform Success: {', '.join(executed_list)}"
                cur.execute("INSERT INTO transform_log (note) VALUES (%s)", (note,))
                conn.commit()
                log("Log saved to transform_log table.")
            except Exception as db_err:
                log(f"Error saving log to DB: {db_err}")

        cur.close()
        conn.close()
    except Exception as e:
        log(f"Database error: {e}")

if __name__ == "__main__":
    main()
