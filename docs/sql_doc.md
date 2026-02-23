# 📜 SQL Sync Scripts Documentation

รายการสคริปต์ SQL ที่ใช้สำหรับดึงข้อมูลจาก HOSxP เพื่อนำเข้าสู่ระบบ Data Transform Pipeline (ตาราง `c_scripts`)

| script_name                                 | description                             | activate  |
| :------------------------------------------ | :-------------------------------------- | :-------: |
| **000_sync_test.sql**                       | สำหรับทดสอบระบบ Sync                    | ✅ Active |
| **001_sync_bed_an_occupancy.sql**           | อัตราครองเตียง (Bed Occupancy)          | ✅ Active |
| **002_sync_bed_type_all.sql**               | จำนวนเตียงแยกตามประเภท                  | ✅ Active |
| **003_sync_critical_wait_bed.sql**          | ระยะเวลารอคอยเตียงวิกฤต                 | ✅ Active |
| **004_sync_drgs_rw_top10.sql**              | 10 อันดับโรคตาม AdjRW                   | ✅ Active |
| **005_sync_drgs_sum.sql**                   | สรุปภาพรวม DRGs                         | ✅ Active |
| **006_sync_icu_semi_icu_case_realtime.sql** | เคส ICU / Semi-ICU Real-time            | ✅ Active |
| **007_sync_icu_ward_death.sql**             | อัตราการเสียชีวิตในตึกวิกฤต             | ✅ Active |
| **008_sync_mortality_ami.sql**              | อัตราการเสียชีวิตด้วยโรค AMI            | ✅ Active |
| **009_sync_mortality_sepsis.sql**           | อัตราการเสียชีวิตด้วยโรค Sepsis         | ✅ Active |
| **010_sync_normal_ward_death.sql**          | อัตราการเสียชีวิตในตึกปกติ              | ✅ Active |
| **011_sync_or_utilization_rate.sql**        | อัตราการใช้ห้องผ่าตัด (OR Utilization)  | ✅ Active |
| **012_sync_refer_paperless.sql**            | ข้อมูลการส่งต่อระบบ Paperless           | ✅ Active |
| **013_sync_refer_top10.sql**                | 10 อันดับการส่งต่อ (Refer)              | ✅ Active |
| **014_sync_waiting_time_cataract.sql**      | Waiting Time รายปี: ต้อกระจก (Cataract) | ✅ Active |
| **015_sync_waiting_time_hernia.sql**        | Waiting Time รายปี: ไส้เลื่อน (Hernia)  | ✅ Active |

---

_Last updated: 2026-02-23 13:41_
