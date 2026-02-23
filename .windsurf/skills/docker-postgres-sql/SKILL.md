---
name: docker-postgres-sql
description: |
  ขั้นตอนการใช้งาน PostgreSQL ผ่าน Docker command —
  ครอบคลุม: การเชื่อมต่อฐานข้อมูล, การรัน query CRUD (Create, Read, Update, Delete),
  การสร้าง/จัดการ table, การสำรองและกู้คืนข้อมูล (backup/restore),
  และ Best Practices สำหรับ development.
---

# Docker PostgreSQL — คู่มือรัน Query CRUD ผ่าน Docker

## รูปแบบคำสั่งหลัก

```bash
# รัน SQL command เดียว
docker exec -it <container_name> psql -U <user> -d <database> -c "<SQL>"

# เข้า interactive psql shell
docker exec -it <container_name> psql -U <user> -d <database>

# รัน SQL จากไฟล์
docker exec -i <container_name> psql -U <user> -d <database> < file.sql
```

> **ตัวอย่างในเอกสารนี้ใช้:**
>
> - Container: `my-postgres`
> - User: `myuser`
> - Database: `mydb`

---

## 1. เชื่อมต่อฐานข้อมูล

### 1.1 เข้า psql shell

```bash
# เข้า interactive shell
docker exec -it my-postgres psql -U myuser -d mydb
```

### 1.2 คำสั่ง psql ที่ใช้บ่อย

```
\l              -- แสดง databases ทั้งหมด
\dt             -- แสดง tables ใน schema ปัจจุบัน
\dt+            -- แสดง tables พร้อมขนาดและ description
\d  <table>     -- แสดงโครงสร้าง table
\d+ <table>     -- แสดงโครงสร้าง table แบบละเอียด
\du             -- แสดง users/roles
\c  <dbname>    -- เปลี่ยน database
\dn             -- แสดง schemas
\di             -- แสดง indexes
\x              -- toggle แสดงผลแบบ expanded (แนวตั้ง)
\timing         -- toggle แสดงเวลาที่ใช้รัน query
\q              -- ออกจาก psql
```

---

## 2. Database & Table Management

### 2.1 จัดการ Database

```bash
# สร้าง database
docker exec -it my-postgres psql -U myuser -c "CREATE DATABASE shop;"

# ลบ database
docker exec -it my-postgres psql -U myuser -c "DROP DATABASE IF EXISTS shop;"

# แสดง databases ทั้งหมด
docker exec -it my-postgres psql -U myuser -c "\l"
```

### 2.2 สร้าง Table (CREATE TABLE)

```bash
docker exec -it my-postgres psql -U myuser -d mydb -c "
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(50) UNIQUE NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"
```

```bash
# Table พร้อม Foreign Key
docker exec -it my-postgres psql -U myuser -d mydb -c "
CREATE TABLE posts (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(200) NOT NULL,
    content     TEXT,
    published   BOOLEAN DEFAULT false,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"
```

### 2.3 แก้ไข Table (ALTER TABLE)

```bash
# เพิ่ม column
docker exec -it my-postgres psql -U myuser -d mydb -c "
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
"

# ลบ column
docker exec -it my-postgres psql -U myuser -d mydb -c "
ALTER TABLE users DROP COLUMN phone;
"

# เปลี่ยน type ของ column
docker exec -it my-postgres psql -U myuser -d mydb -c "
ALTER TABLE users ALTER COLUMN username TYPE VARCHAR(100);
"

# เพิ่ม NOT NULL constraint
docker exec -it my-postgres psql -U myuser -d mydb -c "
ALTER TABLE users ALTER COLUMN email SET NOT NULL;
"

# เปลี่ยนชื่อ column
docker exec -it my-postgres psql -U myuser -d mydb -c "
ALTER TABLE users RENAME COLUMN username TO name;
"

# เปลี่ยนชื่อ table
docker exec -it my-postgres psql -U myuser -d mydb -c "
ALTER TABLE users RENAME TO members;
"
```

### 2.4 ลบ Table (DROP TABLE)

```bash
docker exec -it my-postgres psql -U myuser -d mydb -c "
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS users;
"
```

### 2.5 ดูโครงสร้าง Table

```bash
# แสดง columns ของ table
docker exec -it my-postgres psql -U myuser -d mydb -c "\d users"

# แสดงแบบละเอียด (รวม storage, description)
docker exec -it my-postgres psql -U myuser -d mydb -c "\d+ users"

# แสดง tables ทั้งหมด
docker exec -it my-postgres psql -U myuser -d mydb -c "\dt"
```

---

## 3. CRUD Operations

### 3.1 CREATE — เพิ่มข้อมูล (INSERT)

```bash
# Insert แถวเดียว
docker exec -it my-postgres psql -U myuser -d mydb -c "
INSERT INTO users (username, email, password)
VALUES ('john', 'john@example.com', 'hashed_password_1');
"

# Insert หลายแถว
docker exec -it my-postgres psql -U myuser -d mydb -c "
INSERT INTO users (username, email, password) VALUES
    ('alice', 'alice@example.com', 'hashed_password_2'),
    ('bob',   'bob@example.com',   'hashed_password_3'),
    ('carol', 'carol@example.com', 'hashed_password_4');
"

# Insert แล้ว return ข้อมูลที่สร้าง
docker exec -it my-postgres psql -U myuser -d mydb -c "
INSERT INTO users (username, email, password)
VALUES ('dave', 'dave@example.com', 'hashed_password_5')
RETURNING id, username, created_at;
"

# Insert ถ้ายังไม่มี (Upsert / ON CONFLICT)
docker exec -it my-postgres psql -U myuser -d mydb -c "
INSERT INTO users (username, email, password)
VALUES ('john', 'john@example.com', 'new_password')
ON CONFLICT (username)
DO UPDATE SET password = EXCLUDED.password, updated_at = CURRENT_TIMESTAMP;
"
```

### 3.2 READ — อ่านข้อมูล (SELECT)

```bash
# ดึงข้อมูลทั้งหมด
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT * FROM users;
"

# เลือก columns
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT id, username, email FROM users;
"

# WHERE — กรองข้อมูล
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT * FROM users WHERE is_active = true;
"

# WHERE พร้อมหลายเงื่อนไข
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT * FROM users
WHERE is_active = true
  AND created_at > '2025-01-01'
  AND email LIKE '%@example.com';
"

# ORDER BY — เรียงข้อมูล
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT * FROM users ORDER BY created_at DESC;
"

# LIMIT & OFFSET — แบ่งหน้า (pagination)
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT * FROM users ORDER BY id LIMIT 10 OFFSET 0;
"

# COUNT — นับจำนวน
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT COUNT(*) FROM users WHERE is_active = true;
"

# GROUP BY — จัดกลุ่ม
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT is_active, COUNT(*) as total
FROM users
GROUP BY is_active;
"

# JOIN — รวมข้อมูลจากหลาย table
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT u.username, p.title, p.created_at
FROM posts p
INNER JOIN users u ON p.user_id = u.id
WHERE p.published = true
ORDER BY p.created_at DESC;
"

# LEFT JOIN
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT u.username, COUNT(p.id) as post_count
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.username
ORDER BY post_count DESC;
"

# Subquery
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT * FROM users
WHERE id IN (SELECT DISTINCT user_id FROM posts WHERE published = true);
"

# DISTINCT — ไม่ซ้ำ
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT DISTINCT email FROM users;
"
```

### 3.3 UPDATE — แก้ไขข้อมูล

```bash
# Update แถวเดียว
docker exec -it my-postgres psql -U myuser -d mydb -c "
UPDATE users
SET email = 'john_new@example.com', updated_at = CURRENT_TIMESTAMP
WHERE username = 'john';
"

# Update หลายแถว
docker exec -it my-postgres psql -U myuser -d mydb -c "
UPDATE users
SET is_active = false, updated_at = CURRENT_TIMESTAMP
WHERE created_at < '2025-01-01';
"

# Update แล้ว return ข้อมูลที่แก้ไข
docker exec -it my-postgres psql -U myuser -d mydb -c "
UPDATE users
SET email = 'updated@example.com', updated_at = CURRENT_TIMESTAMP
WHERE id = 1
RETURNING id, username, email, updated_at;
"

# Update ด้วย subquery
docker exec -it my-postgres psql -U myuser -d mydb -c "
UPDATE posts
SET published = true, updated_at = CURRENT_TIMESTAMP
WHERE user_id = (SELECT id FROM users WHERE username = 'john');
"
```

### 3.4 DELETE — ลบข้อมูล

```bash
# ลบแถวเดียว
docker exec -it my-postgres psql -U myuser -d mydb -c "
DELETE FROM users WHERE id = 5;
"

# ลบหลายแถว
docker exec -it my-postgres psql -U myuser -d mydb -c "
DELETE FROM users WHERE is_active = false;
"

# ลบแล้ว return ข้อมูลที่ลบ
docker exec -it my-postgres psql -U myuser -d mydb -c "
DELETE FROM users WHERE id = 3 RETURNING *;
"

# ลบทุกแถวใน table (ใช้ TRUNCATE เร็วกว่า DELETE)
docker exec -it my-postgres psql -U myuser -d mydb -c "
TRUNCATE TABLE posts RESTART IDENTITY CASCADE;
"
```

> **⚠️ คำเตือน:** `DELETE` ที่ไม่มี `WHERE` จะลบข้อมูลทั้งหมดใน table!
> ให้ใช้ `RETURNING *` เพื่อตรวจสอบข้อมูลที่จะถูกลบ

---

## 4. Index & Constraints

### 4.1 สร้าง Index

```bash
# Index ปกติ
docker exec -it my-postgres psql -U myuser -d mydb -c "
CREATE INDEX idx_users_email ON users(email);
"

# Unique Index
docker exec -it my-postgres psql -U myuser -d mydb -c "
CREATE UNIQUE INDEX idx_users_username ON users(username);
"

# Composite Index (หลาย columns)
docker exec -it my-postgres psql -U myuser -d mydb -c "
CREATE INDEX idx_posts_user_published ON posts(user_id, published);
"

# ลบ Index
docker exec -it my-postgres psql -U myuser -d mydb -c "
DROP INDEX IF EXISTS idx_users_email;
"

# แสดง Indexes ทั้งหมด
docker exec -it my-postgres psql -U myuser -d mydb -c "\di"
```

### 4.2 เพิ่ม Constraints

```bash
# UNIQUE constraint
docker exec -it my-postgres psql -U myuser -d mydb -c "
ALTER TABLE users ADD CONSTRAINT unique_email UNIQUE (email);
"

# CHECK constraint
docker exec -it my-postgres psql -U myuser -d mydb -c "
ALTER TABLE users ADD CONSTRAINT check_username_length CHECK (LENGTH(username) >= 3);
"

# ลบ constraint
docker exec -it my-postgres psql -U myuser -d mydb -c "
ALTER TABLE users DROP CONSTRAINT IF EXISTS check_username_length;
"
```

---

## 5. Aggregate & Utility Queries

### 5.1 Aggregate Functions

```bash
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT
    COUNT(*)                    AS total_users,
    COUNT(*) FILTER (WHERE is_active) AS active_users,
    MIN(created_at)             AS oldest_account,
    MAX(created_at)             AS newest_account
FROM users;
"
```

### 5.2 ตรวจสอบขนาด Database / Table

```bash
# ขนาด database
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT pg_size_pretty(pg_database_size('mydb'));
"

# ขนาดแต่ละ table
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC;
"

# จำนวนแถวแต่ละ table (ประมาณ)
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT relname AS table, n_live_tup AS row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
"
```

### 5.3 ดู Active Connections

```bash
docker exec -it my-postgres psql -U myuser -d mydb -c "
SELECT pid, usename, datname, state, query
FROM pg_stat_activity
WHERE datname = 'mydb';
"
```

---

## 6. รัน SQL จากไฟล์

```bash
# รัน SQL file จาก host
docker exec -i my-postgres psql -U myuser -d mydb < script.sql

# รัน SQL file ที่อยู่ภายใน container
docker exec -it my-postgres psql -U myuser -d mydb -f /tmp/script.sql

# Copy ไฟล์เข้า container แล้วรัน
docker cp script.sql my-postgres:/tmp/script.sql
docker exec -it my-postgres psql -U myuser -d mydb -f /tmp/script.sql
```

---

## 7. Backup & Restore

### 7.1 Backup

```bash
# Backup เป็น SQL
docker exec -t my-postgres pg_dump -U myuser -d mydb > backup.sql

# Backup เฉพาะ schema
docker exec -t my-postgres pg_dump -U myuser -d mydb --schema-only > schema.sql

# Backup เฉพาะ data
docker exec -t my-postgres pg_dump -U myuser -d mydb --data-only > data.sql

# Backup เฉพาะ table
docker exec -t my-postgres pg_dump -U myuser -d mydb -t users > users_backup.sql

# Backup แบบ compressed
docker exec -t my-postgres pg_dump -U myuser -d mydb -Fc > backup.dump
```

### 7.2 Restore

```bash
# Restore จาก SQL
docker exec -i my-postgres psql -U myuser -d mydb < backup.sql

# Restore จาก compressed dump
docker exec -i my-postgres pg_restore -U myuser -d mydb --no-owner < backup.dump
```

---

## Quick Reference

```bash
# ═══════════ เชื่อมต่อ ═══════════
docker exec -it my-postgres psql -U myuser -d mydb

# ═══════════ CREATE ═══════════
docker exec -it my-postgres psql -U myuser -d mydb -c "INSERT INTO t (col) VALUES ('val') RETURNING *;"

# ═══════════ READ ═══════════
docker exec -it my-postgres psql -U myuser -d mydb -c "SELECT * FROM t WHERE condition;"

# ═══════════ UPDATE ═══════════
docker exec -it my-postgres psql -U myuser -d mydb -c "UPDATE t SET col='val' WHERE id=1 RETURNING *;"

# ═══════════ DELETE ═══════════
docker exec -it my-postgres psql -U myuser -d mydb -c "DELETE FROM t WHERE id=1 RETURNING *;"

# ═══════════ ดูโครงสร้าง ═══════════
docker exec -it my-postgres psql -U myuser -d mydb -c "\dt"       # list tables
docker exec -it my-postgres psql -U myuser -d mydb -c "\d users"  # describe table

# ═══════════ Backup / Restore ═══════════
docker exec -t my-postgres pg_dump -U myuser -d mydb > backup.sql
docker exec -i my-postgres psql -U myuser -d mydb < backup.sql

# ═══════════ รัน SQL file ═══════════
docker exec -i my-postgres psql -U myuser -d mydb < script.sql
```
