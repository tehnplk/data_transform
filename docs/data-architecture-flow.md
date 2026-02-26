# Data Architecture Flow: Raw to Transform

เอกสารนี้อธิบายสถาปัตยกรรมข้อมูล (Data Architecture) ของระบบการรับฝากและแปลงข้อมูล (ETL Process) ซึ่งประกอบด้วย 3 ส่วนหลัก ได้แก่ ตาราง `raw` (Staging/Landing Zone), สคริปต์ Python (Processing Engine), และตาราง `transform_sync_*` (Data Warehouse/Serving Layer)

## 1. ตาราง `raw` (Staging / Landing Zone)

ตาราง `raw` ทำหน้าที่เป็นจุดรับข้อมูลแรกสุด (Buffer) ที่เชื่อมต่อข้ามมาจากแหล่งข้อมูลต้นทาง (เช่น โรงพยาบาลระดับต่างๆ) โดยโครงสร้างถูกออกแบบมาให้มีความยืดหยุ่นสูง เพื่อรองรับข้อมูลที่หลากหลายรูปแบบและลดปัญหาเมื่อฝั่งต้นทางมีการเปลี่ยน Data Structure

### โครงสร้างตาราง `raw`

- `hoscode` (VARCHAR): รหัสสถานพยาบาล
- `payload` (JSONB): ข้อมูลทางธุรกิจทั้งหมด ถูกบรรจุรวมกันอยู่ในรูปแบบ JSON
- `source` (VARCHAR): แหล่งที่มาของข้อมูลต้นทาง (เช่น `001_sync_bed_an_occupancy.sql`) ตัวแปรนี้จะใช้เป็นตัวระบุว่าข้อมูลก้อนนี้ จะต้องนำไปรับมือด้วยสคริปต์ Python ตัวใด และจะถูกจับไปลงตาราง `transform_sync_*` ชื่ออะไร
- `sync_datetime` (TIMESTAMPTZ): เวลาที่ข้อมูลถูกดึง/ถูกส่ง เข้ามาบันทึกในระบบ
- `transform_datetime` (TIMESTAMPTZ): **ตัวชี้วัดสถานะการประมวลผล** จะมีค่าตั้งต้นเป็น `NULL` สำหรับข้อมูลที่เพิ่งเข้ามาใหม่ และจะถูกระบุเวลา/Stamp เมื่อสคริปต์ Python นำข้อมูลชุดนี้ไปแปลงลงตารางปลายทางเสร็จสิ้นแล้ว

## 2. Python Scripts (The Process Engine)

สคริปต์ Python (เช่น `001_sync_bed_an_occupancy.py`) ทำหน้าที่เป็นตัวกลางในการทำ **ETL Pipeline** เชื่อมโยงข้อมูลระหว่างฝั่งดิบ `raw` เข้าสู่ Database ที่พร้อมใช้งานเชิงระบบที่ `transform`

### กระบวนการทำงาน (Workflow) เชิงลึก

1. **Extract**: สคริปต์จะเริ่มทำงานโดย Query ค้นหาข้อมูลในตาราง `raw` ภายใต้เงื่อนไข `transform_datetime IS NULL` (ยังไม่ประมวลผล) และมี `source` ตรงกับที่สคริปต์ตัวนั้นๆ ถูกมอบหมายให้รับผิดชอบ
2. **Transform (Dynamic Mapping)**:
   - โปรแกรมจะเริ่มทำการกระจาย (Flatten) ข้อมูลก้อนในคอลัมน์ `payload` (JSONB) ออกมาเป็นค่ารายฟิลด์
   - ระบบจะดึงโครงสร้างของตารางเป้าหมาย (`transform_sync_*`) มาโดยอัตโนมัติ ผ่าน `information_schema.columns` (ไม่ต้อง Hardcode ชื่อฟิลด์)
   - สคริปต์จะจับคู่ค่า Key ใน JSON ตามชื่อให้ตรงกับชื่อคอลัมน์ของตารางปลายทางแบบอัตโนมัติ พร้อมทั้งตรวจสอบและแปลง Data Type (เช่น String, Date, Integer) ให้ถูกต้องตามข้อกำหนดของคอลัมน์ในฐานข้อมูล (Dynamic Type Casting)
3. **Load (UPSERT)**: นำชุดข้อมูลที่จัดการเรียบร้อย ทยอย Load ลงตารางเป้าหมาย `transform_sync_*`
   - หากเป็นข้อมูลบรรทัดใหม่ จะทำการ `INSERT`
   - ระบบจะจำลองหาข้อผิดพลาดกรณีข้อมูลซ้อนทับกัน (Conflict) โดยอาศัยเงื่อนไข Primary Key ของแต่ละตารางเป้าหมาย (มักซ้อนเป็น Composite Key หลายฟิลด์) หากเจอ Key ประวัติซ้ำกัน มันจะพิจารณาทำการเขียนทับ (`UPDATE`) ข้อมูลที่ใหม่กว่าเข้าไปแทน (โดยเช็คจากเวลาอัปเดตต้นทาง คือคอลัมน์ `d_update` ใน JSON)
4. **Mark as Processed**: กลับไปที่ตาราง `raw` เพื่อปรับปรุงอัปเดตเวลาลงคอลัมน์ `transform_datetime` ตามเวลาปัจจุบัน (`now()`) เพื่อให้หลุดพ้นจากเงื่อนไขในข้อ 1. ถือเป็นการปิดลูป ETL วงจรนั้น

## 3. ตาราง `transform_sync_*` (Data Warehouse / Serving Layer)

ทำหน้าที่เป็นชั้นคลังข้อมูลที่พร้อมเสิร์ฟให้แก่ผู้ใช้งานและบริการภายนอก เช่น ดาต้าโมเดลสำหรับ Dashboard หรือ KPI Service โดยโครงสร้างการจัดเก็บ (Schema) จะถูกออกแบบระบุชนิดระบุตัวแปรเอาไว้ชัดเจน

### คุณลักษณะที่สำคัญ

- **โครงสร้างแบบตายตัว (Fix Structure)**: ทุกตารางมีการระบุ Column และ Data Type เอาไว้อย่างชัดเจน ใช้งานต่อยอดได้ทันที
- **คอลัมน์อัปเดต (`d_update`)**: เป็นเขตข้อมูลสากลที่มีในเกือบทุกตาราง เพื่อใช้ประเมินความใหม่เก่าของข้อมูล
- **Primary Key แบบผสม (Composite Primary Key)**: เพื่อรับมือกับการที่ข้อมูลไม่มีหมายเลข ID วิ่งกำกับเป็นรายบรรทัด (เช่นชุดข้อมูลสถิติรายเดือน) ระบบจึงถูก Design ให้ใช้ Primary Key ก้อนใหญ่ ที่มัดรวมขึ้นมาจากหลายคอลัมน์ เช่น:
  - `transform_sync_dental_monthly`: รวม `hoscode` + `y` + `m`
  - `transform_sync_drgs_rw_top10`: รวม `hoscode` + `y` + `m` + `drgs_code`
  - `transform_sync_bed_an_occupancy`: รวม `hoscode` + `an_censored` + `bedno` + `export_code` + `regdate` + `dchdate`

## สรุปภาพรวม Data Pipeline

```mermaid
graph LR
    A[แหล่งข้อมูลง<br/>เช่น โรงพยาบาล] -->|API / Sync| B(ตาราง 'raw'<br>payload: JSONB<br>transform_datetime: NULL)
    B -.->|Python (Cronjob)| C[แกะ JSONB<br/>แปลง Data Type<br/>ลบข้อมูลซ้ำ]
    C -->|UPSERT<br/>ยึดตาม Composite PK| D{ตาราง 'transform_sync_*'<br/>ข้อมูลมีโครงสร้างชัดเจน<br/>พร้อมใช้งาน}
    C -.->|ชี้เวลาเสร็จสิ้น| E(ตาราง 'raw'<br/>transform_datetime = NOW)

    style B fill:#ffeaa7,stroke:#fdcb6e,stroke-width:2px;
    style C fill:#81ecec,stroke:#00cec9,stroke-width:2px;
    style D fill:#55efc4,stroke:#00b894,stroke-width:2px;
    style E fill:#ecf0f1,stroke:#bdc3c7,stroke-width:1px;
```
