# 📊 PLK Data Sync & Transform Pipeline

## Server: `adminplk@61.19.112.242:2233` (tehn-project)

---

## 🔄 System Flow Overview

```
┌─────────────┐     HTTP POST /raw      ┌──────────────────────┐
│             │ ─────────────────────▶  │                      │
│   HOSxP     │      (per hospital)     │  FastAPI (uvicorn)   │
│  Hospital   │                         │  Port: 8000          │
│  11251      │                         │  /home/adminplk/     │
│  11252      │     Endpoints:          │  plk-sync-server/    │
│  11253      │     POST /raw           │  main.py             │
│             │     GET  /health        │                      │
│             │     GET  /check_last    │                      │
└─────────────┘                         └──────────┬───────────┘
                                                   │
                                                   │ INSERT INTO raw
                                                   ▼
                                        ┌──────────────────────┐
                                        │  PostgreSQL 17       │
                                        │  Docker: postgres_17_db
                                        │  Port: 5433          │
                                        │  DB: datacenter      │
                                        │                      │
                                        │  ┌────────────────┐  │
                                        │  │   raw table     │  │
                                        │  │                 │  │
                                        │  │ hoscode         │  │
                                        │  │ source          │  │
                                        │  │ payload (jsonb) │  │
                                        │  │ sync_datetime   │  │
                                        │  │ transform_datetime│ │
                                        │  └───────┬────────┘  │
                                        │          │           │
                                        └──────────┼───────────┘
                                                   │
                              Cron: */30 * * * *   │
                              run_all_transforms.sh│
                                                   ▼
                                        ┌──────────────────────┐
                                        │  Python Transform    │
                                        │  Scripts (00-15)     │
                                        │  /home/adminplk/     │
                                        │  transform/          │
                                        │                      │
                                        │  Logic:              │
                                        │  1. READ raw         │
                                        │  2. DEDUPLICATE      │
                                        │  3. UPSERT into      │
                                        │     transform_sync_* │
                                        │  4. STAMP raw        │
                                        │  5. DELETE raw       │
                                        └──────────┬───────────┘
                                                   │
                                                   │ UPSERT (ON CONFLICT DO UPDATE)
                                                   ▼
                                        ┌──────────────────────┐
                                        │  Target Tables       │
                                        │  (transform_sync_*)  │
                                        │                      │
                                        │  PK: all columns     │
                                        │  except d_update     │
                                        └──────────────────────┘
```

---

## 📋 Data Flow Steps

### Step 1: Data Ingestion (Real-time)

| Item           | Detail                                      |
| :------------- | :------------------------------------------ |
| **Source**     | HOSxP (Hospital Information System)         |
| **Method**     | HTTP `POST /raw`                            |
| **Receiver**   | FastAPI + Uvicorn (port 8000)               |
| **Storage**    | `raw` table (PostgreSQL)                    |
| **Log**        | `/home/adminplk/plk-sync-server/server.log` |
| **Log Rotate** | logrotate daily, max 10MB, keep 7 files     |

### Step 2: Data Transformation (Cron - every 30 min)

| Item         | Detail                                      |
| :----------- | :------------------------------------------ |
| **Trigger**  | Cron `*/30 * * * *`                         |
| **Script**   | `run_all_transforms.sh`                     |
| **Location** | `/home/adminplk/transform/`                 |
| **Log**      | `~/transform/logs/transform_YYYYMMDD.log`   |
| **Method**   | **UPSERT** (`INSERT ON CONFLICT DO UPDATE`) |

### Step 3: Safety Mechanisms

| Safety Feature        | Description                                    |
| :-------------------- | :--------------------------------------------- |
| **Read Before Write** | Data is read from `raw` FIRST into memory      |
| **Conditional Write** | Only writes if new data exists                 |
| **No Data Loss**      | If `raw` is empty, target table is preserved   |
| **Upsert**            | Existing rows are updated, new rows inserted   |
| **Composite PK**      | All columns (except d_update) form the PK      |
| **Backup**            | Original scripts backed up as `.bak` / `.bak2` |

---

## 📁 Transform Scripts Mapping

| Script                                  | Source (in raw)                         | Target Table                                | PK Columns                                                                                                                                                                                 |
| :-------------------------------------- | :-------------------------------------- | :------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `00_sync_test.py`                       | `0_sync_test.sql`                       | `transform_sync_test`                       | hoscode, version                                                                                                                                                                           |
| `01_sync_bed_an_occupancy.py`           | `1_sync_bed_an_occupancy.sql`           | `transform_sync_bed_an_occupancy`           | hoscode, an_censored, bedno, export_code, regdate, dchdate, calc_start, calc_end, overlap_days, roomno                                                                                     |
| `02_sync_bed_type_all.py`               | `2_sync_bed_type_all.sql`               | `transform_sync_bed_type_all`               | hoscode + other columns                                                                                                                                                                    |
| `03_sync_critical_wait_bed.py`          | `3_sync_critical_wait_bed.sql`          | `transform_sync_critical_wait_bed`          | hoscode, yr, yr_be, total_cases, admitted_cases, refer_out_cases, avg_wait_min, avg_wait_hours, avg_admit_wait_min, avg_admit_wait_hr, avg_refer_wait_min, avg_refer_wait_hr, pct_over_4hr |
| `04_sync_drgs_rw_top10.py`              | `4_sync_drgs_rw_top10.sql`              | `transform_sync_drgs_rw_top10`              | hoscode, y, m, drgs_code, sum_adj_rw                                                                                                                                                       |
| `05_sync_drgs_sum.py`                   | `5_sync_drgs_sum.sql`                   | `transform_sync_drgs_sum`                   | hoscode, y, m, num_pt, sum_adjrw, cmi                                                                                                                                                      |
| `06_sync_icu_semi_icu_case_realtime.py` | `6_sync_icu_semi_icu_case_realtime.sql` | `transform_sync_icu_semi_icu_case_realtime` | hoscode, icu_case                                                                                                                                                                          |
| `08_sync_mortality_ami.py`              | `8_sync_mortality_ami.sql`              | `transform_sync_mortality_ami`              | hoscode, discharge_year, total_admissions, deaths, mortality_rate_pct                                                                                                                      |
| `09_sync_mortality_sepsis.py`           | `9_sync_mortality_sepsis.sql`           | `transform_sync_mortality_sepsis`           | hoscode, discharge_year, total_admissions, deaths, mortality_rate_pct                                                                                                                      |
| `10_sync_normal_ward_death.py`          | `10_sync_normal_ward_death.sql`         | `transform_sync_normal_ward_death`          | hoscode, y, pdx, pdx_name, death_count                                                                                                                                                     |
| `11_sync_or_utilization_rate.py`        | `11_sync_or_utilization_rate.sql`       | `transform_sync_or_utilization_rate`        | hoscode, op_year, op_year_be, total_cases, total_or_minutes, avg_min_per_case, total_or_hours, actual_or_days, avail_min_1room, util_pct                                                   |
| `12_sync_refer_paperless.py`            | `12_sync_refer_paperless.sql`           | `transform_sync_refer_paperless`            | hoscode, y, m, refer_out_count, moph_refer_count                                                                                                                                           |
| `13_sync_refer_top10.py`                | `13_sync_refer_top10.sql`               | `transform_sync_refer_top10`                | hoscode, icd10, icd10_name, total_refer                                                                                                                                                    |
| `14_sync_waiting_time_cataract.py`      | `14_sync_waiting_time_cataract.sql`     | `transform_sync_waiting_time_cataract`      | hoscode, visit_year, total_appointments, avg_wait_days, min_wait_days, max_wait_days, avg_wait_weeks                                                                                       |
| `15_sync_waiting_time_hernia.py`        | `15_sync_waiting_time_hernia.sql`       | `transform_sync_waiting_time_hernia`        | hoscode, visit_year, total_appointments, avg_wait_days, min_wait_days, max_wait_days, avg_wait_weeks                                                                                       |

---

## 🏥 Hospitals Sending Data

| Hoscode   | Status                         |
| :-------- | :----------------------------- |
| **11251** | ✅ Active - ส่งข้อมูลประจำ     |
| **11252** | ✅ Active - ส่งข้อมูลประจำ     |
| **11253** | ✅ Active - เริ่มส่งข้อมูลใหม่ |

---

## 🛠️ Infrastructure

```
┌────────────────────────────────────────────────┐
│              Ubuntu Server (tehn-project)       │
│              61.19.112.242:2233                 │
│                                                 │
│  ┌──────────────────┐  ┌─────────────────────┐ │
│  │ Docker Containers│  │ PM2 Processes       │ │
│  │                  │  │                     │ │
│  │ • postgres_17_db │  │ • kpi (Node.js)     │ │
│  │   Port: 5433     │  │                     │ │
│  │                  │  │                     │ │
│  │ • pgadmin        │  │                     │ │
│  │                  │  │                     │ │
│  │ • mysql8         │  └─────────────────────┘ │
│  └──────────────────┘                           │
│                                                 │
│  ┌──────────────────┐  ┌─────────────────────┐ │
│  │ uvicorn (nohup)  │  │ Cron Jobs           │ │
│  │                  │  │                     │ │
│  │ FastAPI          │  │ */30 * * * *        │ │
│  │ Port: 8000       │  │ run_all_transforms  │ │
│  │ server.log       │  │                     │ │
│  │ (logrotate)      │  │ Logs:               │ │
│  └──────────────────┘  │ ~/transform/logs/   │ │
│                         └─────────────────────┘ │
└────────────────────────────────────────────────┘
```

---

## 📝 Key Directories

| Path                               | Purpose                               |
| :--------------------------------- | :------------------------------------ |
| `/home/adminplk/plk-sync-server/`  | FastAPI app รับข้อมูลจาก HOSxP        |
| `/home/adminplk/transform/`        | Python scripts สำหรับ Transform       |
| `/home/adminplk/transform/logs/`   | Log ของ Transform (daily)             |
| `/etc/logrotate.d/plk-sync-server` | Log rotation config สำหรับ server.log |

---

## 🔧 Useful Commands

```bash
# ดูข้อมูลค้างใน raw
docker exec postgres_17_db psql -U admin -d datacenter \
  -c "SELECT source, hoscode, COUNT(*) FROM raw GROUP BY source, hoscode;"

# รัน Transform ทั้งหมด
bash /home/adminplk/transform/run_all_transforms.sh

# รัน Transform เฉพาะ source
python3 /home/adminplk/transform/04_sync_drgs_rw_top10.py

# เช็คสถานะ Transform ทุกตาราง
python3 /home/adminplk/transform/check_status.py

# นับข้อมูลแยก รพ.ทุกตาราง
python3 /home/adminplk/transform/count_by_hos.py

# ดู Cron jobs
crontab -l

# ดู Log วันนี้
tail -50 ~/transform/logs/transform_$(date +%Y%m%d).log
```

---

_Last updated: 2026-02-17_
