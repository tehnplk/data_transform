---
name: hosxp
description: Use this skill when working with HOSxP Hospital Information System database running on MariaDB container. Trigger this skill when users need to query patient data, population statistics, OPD/IPD records, disease analysis, or generate public health reports from HOSxP database.
license: MIT
---

# HOSxP Database Skill

## Database Connection

| Parameter | Value      |
| --------- | ---------- |
| Container | `mariadb`  |
| User      | `root`     |
| Password  | `112233`   |
| Database  | `hos11253` |

## Usage

### เชื่อมต่อฐานข้อมูล

ใช้ `docker-mariadb-sql` skill สำหรับการรัน SQL queries:

```bash
docker exec -i mariadb mysql --default-character-set=utf8 -uroot -p112233 hos11253 -e "SELECT ..."
```

หมายเหตุ (PowerShell): หากต้องการรัน SQL จากไฟล์ บน Windows PowerShell ใช้การ pipe แทนการ redirect ด้วย `<`

```powershell
Get-Content .\query.sql | docker exec -i mariadb mysql --default-character-set=utf8 -uroot -p112233 hos11253
```

### ค้นหาความสัมพันธ์ของตาราง

ใช้ `notebooklm` skill เพื่อวิเคราะห์โครงสร้างและความสัมพันธ์ระหว่างตาราง

## Examples

### ตัวอย่างที่ 1: นับจำนวนประชากรแยกรายหมู่บ้าน

```sql
SELECT
    v.village_moo AS หมู่ที่,
    v.village_name AS ชื่อหมู่บ้าน,
    COUNT(p.person_id) AS จำนวนประชากร
FROM person p
LEFT JOIN village v ON v.village_id = p.village_id
WHERE p.house_regist_type_id IN (1, 3)
  AND p.person_id IS NOT NULL
GROUP BY v.village_moo, v.village_name
ORDER BY CAST(v.village_moo AS UNSIGNED);
```

### ตัวอย่างที่ 2: นับจำนวนประชากรแยกรายตำบล

```sql
SELECT
    t.name AS ตำบล,
    COUNT(p.person_id) AS จำนวนประชากร
FROM person p
LEFT JOIN village v ON v.village_id = p.village_id
LEFT JOIN thaiaddress t ON t.addressid = v.address_id
WHERE p.house_regist_type_id IN (1, 3)
  AND p.person_id IS NOT NULL
GROUP BY t.name
ORDER BY จำนวนประชากร DESC;
```

### ตัวอย่างที่ 3: นับจำนวนผู้ป่วยโรคทางเดินหายใจ

```sql
SELECT
    COUNT(DISTINCT o.hn) AS จำนวนผู้ป่วย,
    YEAR(o.vstdate) AS ปี,
    MONTH(o.vstdate) AS เดือน
FROM ovstdiag od
JOIN ovst o ON o.vn = od.vn
WHERE od.icd10 LIKE 'J%'
  AND YEAR(o.vstdate) = 2568
GROUP BY YEAR(o.vstdate), MONTH(o.vstdate)
ORDER BY ปี, เดือน;
```

### ตัวอย่างที่ 4: ดึงข้อมูลผู้ป่วยพร้อมที่อยู่แบบเต็ม

```sql
SELECT
    p.hn,
    p.cid,
    CONCAT(p.pname, p.fname, ' ', p.lname) AS patient_name,
    p.addrpart AS house_no,
    p.moopart AS moo,
    t3.name AS tambon,
    t2.name AS amphur,
    t1.name AS changwat
FROM patient p
-- ดึงชื่อตำบล (รหัสจังหวัด 2 หลัก + อำเภอ 2 หลัก + ตำบล 2 หลัก)
LEFT JOIN thaiaddress t3 ON t3.addressid = CONCAT(p.chwpart, p.amppart, p.tmbpart)
-- ดึงชื่ออำเภอ (รหัสจังหวัด 2 หลัก + อำเภอ 2 หลัก + '00')
LEFT JOIN thaiaddress t2 ON t2.addressid = CONCAT(p.chwpart, p.amppart, '00')
-- ดึงชื่อจังหวัด (รหัสจังหวัด 2 หลัก + '0000')
LEFT JOIN thaiaddress t1 ON t1.addressid = CONCAT(p.chwpart, '0000')
LIMIT 10;
```

## Best Practices

1. **Character Encoding**: ใช้ `--default-character-set=utf8` เพื่อแสดงผลภาษาไทยได้ถูกต้อง
2. **Performance**: ใช้ `LIMIT` เมื่อทดสอบ query ครั้งแรก
3. **Date Filtering**: ระวังปี พ.ศ. vs ค.ศ. ในฐานข้อมูล HOSxP มักใช้ ค.ศ.
4. **ICD-10 Codes**: โรคทางเดินหายใจเริ่มด้วย 'J', โรคติดเชื้อเริ่มด้วย 'A' หรือ 'B'
5. **Table Relationships**: ใช้ `notebooklm` skill เพื่อทำความเข้าใจโครงสร้างตารางก่อนเขียน query ซับซ้อน

## Common Tables

### กลุ่มตาราง ทะเบียนประชากรและที่อยู่

ใช้ **`hn`** เป็นคีย์หลักในการระบุตัวตนและเชื่อมโยงไปยังระบบบริการอื่นๆ

- `patient`: ตารางหลักเก็บประวัติส่วนตัวผู้ป่วย (HN, CID, ชื่อ-นามสกุล, วันเกิด) และข้อมูลที่อยู่พื้นฐาน
- `thaiaddress`: ตารางรหัสที่อยู่มาตรฐาน (ตำบล/อำเภอ/จังหวัด) เชื่อมกับ `patient` ด้วย `chwpart`, `amppart`, `tmbpart`
- `village`: ข้อมูลหมู่บ้านในเขตรับผิดชอบ (เชื่อมกับ `person` ด้วย `village_id`)
- `person`: ข้อมูลประชากรในเขตรับผิดชอบ (เชิงรุก) เชื่อมกับ `patient` ด้วย `patient_hn`
- **ตาราง Lookup อื่นๆ:** `sex` (เพศ), `occupation` (อาชีพ), `nationality` (สัญชาติ), `religion` (ศาสนา)

### กลุ่มตาราง ทะเบียนผู้ป่วยและการรักษาที่ OPD

ใช้ **`vn` (Visit Number)** เป็นคีย์หลักในการเชื่อมโยงเหตุการณ์การรับบริการในแต่ละครั้ง

- `ovst`: ตารางหลักการรับบริการผู้ป่วยนอก (เก็บ VN, HN, วันเวลาที่มา, แผนก/คลินิก, แพทย์ผู้ตรวจ)
- `opdscreen`: บันทึกการซักประวัติและสัญญาณชีพ (BP, Weight, Height, CC, HPI) เชื่อมด้วย `vn`
- `vn_stat`: ตารางสรุปข้อมูลสถิติราย Visit (โรคหลัก PDX, ค่าใช้จ่ายรวม, สิทธิการรักษา)
- `ovstdiag`: บันทึกการวินิจฉัยโรคราย Visit (ICD-10 และประเภทการวินิจฉัย)
- `opitemrece`: รายละเอียดค่าใช้จ่ายรายรายการ (ยา, เวชภัณฑ์, ค่าบริการ) เชื่อมด้วย `vn` หรือ `an`
- `pttype`: Lookup สิทธิการรักษา (เชื่อมกับ `ovst.pttype`)
- `oapp`: ข้อมูลนัดหมาย (เก็บวันที่นัด `nextdate`, คลินิกที่นัด, แพทย์ผู้นัด)

### กลุ่มตาราง IPD

ตารางผู้ป่วยในมีศูนย์กลางอยู่ที่ **`an` (Admission Number)** ซึ่งเชื่อมโยงข้อมูลทั้งหมดของการนอนโรงพยาบาลครั้งนั้นๆ

- **ตารางหลักและการรับตัว:**
  - `ipt`: ตารางหลักเก็บข้อมูลการแอดมิท (เชื่อม `patient.hn` และ `ovst.vn`)
  - `an_stat`: ตารางสรุปสถิติสำคัญราย `an` (PDX, วันนอน, ค่าใช้จ่าย, DRG) - **แนะนำใช้ทำรายงาน**
  - `iptadm`: สถานะการครองตึก/เตียงปัจจุบันของ `an` นั้นๆ
- **ตารางสถานที่พัก (Hierarchy: Ward -> Room -> Bed):**
  - `ward`: แฟ้มข้อมูลตึกผู้ป่วย
  - `roomno`: แฟ้มข้อมูลห้องพัก (เชื่อม `ward`)
  - `bedno`: ทะเบียนเตียง (เชื่อม `roomno`) จัดกลุ่มตาม export_code หลักที่ 4
  - `iptbedmove`: ประวัติการย้ายเตียง/ย้ายตึก
- **ข้อมูลทางคลินิกและสถิติ DRG:**
  - `iptdiag`: การวินิจฉัยโรค IPD (เชื่อมด้วย `an`)
  - `iptoprt`: ข้อมูลการทำหัตถการ/ผ่าตัด (เชื่อมด้วย `an`)
  - `ipt` (ฟิลด์ `rw`, `adjrw`): ค่า RW/AdjRW สำหรับคำนวณ CMI
  - `ipt_drg_result`: รายละเอียดผลประมวลผล DRG แยกตาม `an`
  - `ipt_bed_stat`: ข้อมูลสถิติการครองเตียง

### กลุ่มตาราง LAB

เชื่อมโยงผ่าน **`lab_order_number`** เป็นคีย์หลักในการควบคุมใบสั่งตรวจ

- `lab_head`: ส่วนหัวของใบสั่งตรวจ Lab (เก็บ HN, VN, วันเวลาสั่ง, แพทย์ผู้สั่ง)
- `lab_order`: รายละเอียดรายการตรวจและผล (เชื่อมด้วย `lab_order_number`, เก็บ `lab_items_code` และผลตรวจ)
- `lab_items`: Master รหัสรายการ Lab (ชื่อรายการ, ค่าปกติ, ราคาค่าบริการ)

### กลุ่มตาราง x-ray

เชื่อมโยงด้วย **`xn` (X-ray Number)** เป็นคีย์หลักกำกับการทำเอกซเรย์

- `xray_head`: ส่วนหัวใบสั่ง X-ray (HN, VN, รายการที่สั่ง, แผนกที่สั่ง)
- `xrayxn`: ตารางกลางเชื่อมความสัมพันธ์ระหว่าง `hn` และ `xn` (รหัสหมายเลขเอกซเรย์)
- `xray_report`: รายงานผลการอ่านฟิล์ม (เชื่อมด้วย `xn`, เก็บข้อความรายงานผล, แพทย์ผู้อ่านผล)
- `xray_items`: Master รหัสรายการ X-ray
- `xray_image`: ตารางเก็บไฟล์รูปภาพ X-ray (เชื่อมด้วย `xn`)

หมายเหตุ: บางหน่วยงานอาจไม่ได้เก็บรายละเอียดรายการที่สั่งใน `xray_order` แต่เก็บเป็นข้อความรวมใน `xray_head.xray_list` (ชนิด `text`) แทน

ตัวอย่าง: ดึงผู้ป่วยที่มีรายการ CXR ในปี 2025 (ค้นจาก `xray_head.xray_list`)

```sql
SELECT
    DATE_FORMAT(xh.order_date,'%Y-%m-%d') AS order_date,
    xh.vn,
    xh.hn,
    CONCAT(IFNULL(p.pname,''), IFNULL(p.fname,''), ' ', IFNULL(p.lname,'')) AS patient_name,
    xh.department_name,
    xh.xray_list
FROM xray_head xh
LEFT JOIN patient p ON p.hn = xh.hn
WHERE YEAR(xh.order_date) = 2025
  AND xh.xray_list LIKE '%CXR%'
ORDER BY xh.order_date, xh.vn
LIMIT 20;
```

### กลุ่มตาราง ทันตกรรม

งานทันตกรรมมีกลุ่มตารางหลักที่ขึ้นต้นด้วย **`dt`** โดยเชื่อมโยงกับระบบหลักผ่าน `hn` และ `vn`

- **ตารางบันทึกการรับบริการ:**
  - `dtmain`: ตารางหลักเก็บข้อมูลการรักษาทางทันตกรรมในแต่ละครั้ง (ศูนย์กลางงานทันตกรรม)
  - `dtdn`: ทะเบียนรหัสประจำตัวทางทันตกรรม (Dental Number - `dn`) ของผู้ป่วย
  - `dt_list`: รายการทันตกรรมที่ผูกกับรหัสรับบริการ (`vn`)
- **ตารางรายละเอียดการตรวจสภาพช่องปาก:**
  - `dtdetailmain`: สรุปผลการตรวจสภาพฟันหรือรอยโรคในแต่ละครั้งที่มารับบริการ
  - `dtdetail2`: รายละเอียดเชิงลึกของสิ่งที่ตรวจพบ (เชื่อมกับ `dtcode`)
  - `dtcode`: ตาราง Master รหัสสภาพฟันและชื่อเรียกต่างๆ
- **ตารางรหัสหัตถการ (Master Data):**
  - `dttm`: รายการหัตถการทันตกรรม (เก็บรหัส ICD-10, ICD-9CM, และ `icode` สำหรับค่าใช้จ่าย)
  - `dttx`: (Legacy/Specific) รายการหัตถการทันตกรรม

### กลุ่มตาราง ER

งานห้องฉุกเฉินเชื่อมโยงข้อมูลผ่าน **`vn` (Visit Number)** เป็นหลัก โดยมี `er_regist` เป็นตารางศูนย์กลาง

- **ตารางหลักและบันทึกการรับบริการ:**
  - `er_regist`: ตารางหลักการลงทะเบียนผู้ป่วย ER (เก็บ `vn`, เวลาเข้า-ออก, ประเภทผู้ป่วย, แพทย์ผู้ตรวจ)
  - `er_nursing_detail`: รายละเอียดการซักประวัติและคัดกรองพยาบาล (เวลาที่มาถึง, Trauma, GCS, pupil, Revisit 48hr)
  - `er_emergency_level`: (หรือ `er_emergency_type`) ระดับความเร่งด่วน/Triage Level
- **การรักษาและหัตถการ:**
  - `er_regist_oper`: รายการหัตถการ/ผ่าตัดเล็กที่ทำใน ER
  - `er_oper_code`: Master data รหัสหัตถการ ER (เชื่อมโยง `icode` และ `icd9cm`)
  - `er_command`: คำสั่งการรักษาของแพทย์ใน ER
- **บันทึกทางการพยาบาล:**
  - `er_nursing_record`: บันทึกปัญหาและผลลัพธ์ทางการพยาบาล
  - `er_activity`: มาตรฐานกิจกรรมทางการพยาบาลใน ER
- **ข้อมูลอื่นที่เกี่ยวข้อง:**
  - `er_period`: ข้อมูลเวร/ช่วงเวลาการทำงานของ ER
  - `er_dch_type`: ประเภทการจำหน่ายจาก ER (เชื่อมโยงกับสถานะการจำหน่าย OPD)

### กลุ่มตาราง REFER

ใช้บันทึกการรับและส่งตัวผู้ป่วย เชื่อมโยงกับรหัสสถานพยาบาลมาตรฐาน (**`hospcode`**)

- **การส่งออกและรับเข้า:**
  - `referout`: ข้อมูลส่งตัวไปรักษาต่อ (เก็บเลขที่ใบส่งตัว `refer_number`, สาเหตุ, การวินิจฉัยเบื้องต้น, แพทย์ผู้ส่ง)
  - `referin`: ข้อมูลรับตัวผู้ป่วยจากที่อื่น (เก็บ `hospcode` ต้นทาง, วันที่รับ, การวินิจฉัย)
  - `refer_cause`: Lookup สาเหตุการส่งต่อ (เชื่อมกับ `referout.refer_cause`)
- **ข้อมูลสนับสนุน:**
  - `hospcode`: Master รหัสและชื่อสถานพยาบาลทั่วประเทศ
  - `moph_refer`: ข้อมูลการส่งต่อผ่านระบบออนไลน์ (IS/Refer Anywhere)

### กลุ่มตาราง การนัดหมาย และ follow up

- `oapp`: ตารางนัดหมายหลัก (เชื่อม `hn` และ `vn`) เก็บวันนัดครั้งถัดไป (`nextdate`), คลินิกที่นัด และสาเหตุการนัด
- `clinicmember`: ทะเบียนผู้ป่วยคลินิกโรคเรื้อรัง (NCD) เก็บสถานะการเป็นสมาชิกคลินิกเฉพาะโรค

### กลุ่มตาราง แผนก คลินิก และห้องตรวจ

- `kskdepartment`: ข้อมูลแผนก/จุดบริการ (รหัสแผนก `depcode`, ชื่อแผนก, สถานะเปิด-ปิด `on_desk`)
- `clinic`: ข้อมูลคลินิกเฉพาะโรค (เชื่อมกับรหัสโรคมาตรฐาน `icd10`)
- `spclty`: ข้อมูลกลุ่มงานหรือสาขาความเชี่ยวชาญทางการแพทย์

### กลุ่มตาราง การฉีดวัคซีน

- `person_vaccine_list`: ประวัติการได้รับวัคซีนของประชากรไนเขต (เชื่อม `person_id` และ `vaccine_type`)
- `ovst_vaccine`: ข้อมูลการฉีดวัคซีนที่มารับบริการที่ OPD (เชื่อมด้วย `vn`)
- `vaccine`: Master ข้อมูลชนิดตัววัคซีนและรหัสมาตรฐาน
- `vaccine_type`: Lookup กลุ่มประเภทของวัคซีน

### กลุ่มตาราง งานส่งเสริมป้องกัน และ special PP

- `pp_special`: บันทึกรหัสกิจกรรมส่งเสริมป้องกันกลุ่มเป้าหมาย (รายบริการ)
- `pp_special_type`: Lookup ประเภทบริการ PP Special
- `provis_ppspecial`: ข้อมูลแมปรหัสมาตรฐานสำหรับการส่งออกข้อมูลภาพรวม

### กลุ่มตาราง การแพทย์แผนไทย

- `cicd10tm`: บันทึกรหัสวินิจฉัยแผนไทย (ICD10TM)
- `ovst_sks_icd10tm`: ข้อมูล ICD10TM สำหรับการเบิกจ่าย
- `icd10tm_operation`: Master รหัสหัตถการทางการแพทย์แผนไทย

### กลุ่มตาราง Telemedicine

- `telehealth_list`: ประวัติการรับบริการผ่านระบบ Telehealth
- `telehealth_type`: ประเภทของบริการทางการแพทย์ทางไกล

### กลุ่มตาราง Lookup พื้นฐาน (รหัสมาตรฐาน)

- `icd101`: รหัสโรคมาตรฐาน ICD-10 (เก็บ `code`, `name` และ `tname` ภาษาไทย)
- `icd9cm1`: รหัสหัตถการมาตรฐาน ICD-9-CM
- `drugitems`: รายการยา (เก็บ `icode`, ชื่อยา, ความแรง, ราคา, และข้อกำหนดการใช้ยา)
- `nondrugitems`: รายการค่าใช้จ่ายอื่นๆ ที่ไม่ใช่ยา (เช่น ค่า Lab, X-ray, ค่าธรรมเนียม)

### กลุ่มตารางโรคไม่ติดต่อเรื้อรัง (NCD)

บริหารจัดการข้อมูลผ่านระบบคัดกรองและทะเบียนคลินิกโรคเรื้อรัง

- **ทะเบียนและการขึ้นบัญชี:**
  - `clinicmember`: ทะเบียนผู้ป่วยที่ขึ้นทะเบียนโรคเรื้อรัง (เชื่อม `hn` เข้ากับ `clinic`) เก็บสถานะการรักษา
  - `clinic_member_status`: Lookup สถานะผู้ป่วย (ยังรักษาอยู่, ขาดยา, ย้าย, เสียชีวิต)
- **ประวัติทางคลินิก NCD:**
  - `fbshistory`: ประวัติระดับน้ำตาลในเลือดสะสมย้อนหลัง (สำหรับผู้ป่วยเบาหวาน)
  - `clinic_visit`: ประวัติการเข้าตรวจที่คลินิกเฉพาะโรคในแต่ละครั้ง
  - `clinic_cormobidity_list`: บันทึกโรคร่วมของผู้ป่วย (เช่น เบาหวานร่วมกับความดัน)
- **การคัดกรอง:** ข้อมูลสำคัญจะถูกดึงจาก `opdscreen` ในฟิลด์เฉพาะ เช่น `bps` (ความดัน), `fbs` (น้ำตาล), `riskdm` (ความเสี่ยง)

## Related Skills

- `docker-mariadb-sql`: สำหรับรัน SQL commands ใน MariaDB container
- `notebooklm`: สำหรับวิเคราะห์โครงสร้างและความสัมพันธ์ของตาราง
