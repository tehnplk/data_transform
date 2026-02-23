---
name: plink-remote-host
description: |
  ขั้นตอนการใช้ plink (PuTTY CLI) เพื่อ SSH เข้า Remote Host จาก Windows —
  ครอบคลุม: การเชื่อมต่อ, การรันคำสั่งบน remote, การส่งไฟล์ (pscp/psftp),
  Port Forwarding, Interactive Session, และ Best Practices สำหรับ Agent.
---

# PuTTY plink — คู่มือ SSH เข้า Remote Host จาก Windows

## รูปแบบคำสั่งหลัก

```powershell

# เปิด Interactive Shell
plink -ssh <user>@<host> -P <port> -pw "<password>"


# ใช้ SSH key แทน password
plink -ssh <user>@<host> -P <port> -i "<path_to_ppk>"

```

> # ⚠️ หมายเหตุสำคัญ:
>
> **ต้องกดปุ่ม Enter ที่คีย์บอร์ดเสมอ หลังจาก Established Connection สำเร็จ เพื่อเริ่มต้น Session! และใช้งาน terminal session เดิมในการรันคำสั่งต่างๆ**

> **ตัวอย่างในเอกสารนี้ใช้:**
>
> - Host: `ip_addr`
> - Port: `2233`
> - User: `sa`
> - Password: `MyP@ssw0rd`

---

## 1. การเชื่อมต่อ (Connection)

### 1.1 เชื่อมต่อแบบ Interactive Shell

```powershell
# เปิด shell บน remote (พิมพ์คำสั่งทีละบรรทัด)
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd"
```

> **หมายเหตุ:** เมื่อเชื่อมต่อครั้งแรก plink จะถาม "Store key in cache? (y/n)"
> ให้ตอบ `y` และกด Enter Keyboard เพื่อบันทึก host key

### 1.2 เชื่อมต่อแบบรันคำสั่งเดียว

```powershell
# รันคำสั่ง ls แล้วดูผลลัพธ์
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "ls -la"

# เช็ค uptime
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "uptime"

# เช็ค disk space
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "df -h"
```

### 1.3 เชื่อมต่อด้วย SSH Key (แนะนำ)

```powershell
# ใช้ PPK file (PuTTY Private Key)
plink -ssh sa@ip_addr -P 2233 -i "C:\Users\Admin\.ssh\my_key.ppk" "ls -la"

# สร้าง key ด้วย puttygen
puttygen -t rsa -b 4096 -o my_key.ppk

# Export public key เพื่อวางบน server
puttygen my_key.ppk -O public-openssh -o my_key.pub
```

### 1.4 Auto-accept Host Key (ครั้งแรก)

```powershell
# ยอมรับ host key อัตโนมัติ (ไม่ต้องกด y)
echo y | plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "echo connected"
```

---

## 2. รันคำสั่งบน Remote

### 2.1 คำสั่งเดียว

```powershell
# ดู process ที่กำลังรัน
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "ps aux | head -20"

# ดู memory usage
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "free -h"

# ดู Docker containers
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "docker ps"
```

### 2.2 หลายคำสั่ง (ใช้ && หรือ ;)

```powershell
# รันหลายคำสั่งต่อกัน (หยุดถ้าคำสั่งก่อน error)
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "cd /home/sa && ls -la && pwd"

# รันหลายคำสั่งต่อกัน (รันทุกคำสั่งไม่สนใจ error)
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "uptime; df -h; free -h"
```

### 2.3 คำสั่งที่มี Pipe และ Redirect

```powershell
# Pipe บน remote
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "cat /var/log/syslog | tail -20"

# Redirect output บน remote
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "echo 'hello' > /tmp/test.txt"

# Grep log บน remote
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "grep 'ERROR' /var/log/app.log | tail -10"
```

### 2.4 รันคำสั่งยาว (Heredoc-style)

```powershell
# ส่ง script ผ่าน stdin
echo "ls -la /home && echo '---' && df -h" | plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd"

# ส่ง Python script ไปรันบน remote
type local_script.py | plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "python3 -"
```

### 2.5 รันคำสั่งแบบ Background (ไม่รอผล)

```powershell
# รันแล้วปล่อยให้ทำงาน background บน remote
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "nohup python3 /home/sa/transform/run_all.py > /tmp/output.log 2>&1 &"
```

---

## 3. การส่งไฟล์ (File Transfer)

### 3.1 pscp — Copy ไฟล์

```powershell
# ═══════════ Upload: Local → Remote ═══════════

# Copy ไฟล์เดียว
pscp -P 2233 -pw "MyP@ssw0rd" C:\local\file.txt sa@ip_addr:/home/sa/

# Copy ทั้ง folder (recursive)
pscp -P 2233 -pw "MyP@ssw0rd" -r C:\local\myfolder sa@ip_addr:/home/sa/

# ═══════════ Download: Remote → Local ═══════════

# Download ไฟล์เดียว
pscp -P 2233 -pw "MyP@ssw0rd" sa@ip_addr:/home/sa/file.txt C:\local\

# Download ทั้ง folder
pscp -P 2233 -pw "MyP@ssw0rd" -r sa@ip_addr:/home/sa/myfolder C:\local\
```

### 3.2 psftp — Interactive File Transfer

```powershell
# เปิด FTP-style session
psftp -P 2233 -pw "MyP@ssw0rd" sa@ip_addr
```

```
# คำสั่งใน psftp
ls                      # list ไฟล์บน remote
lcd C:\local            # เปลี่ยน local directory
cd /home/sa       # เปลี่ยน remote directory
put file.txt            # upload ไฟล์
get file.txt            # download ไฟล์
mput *.py               # upload หลายไฟล์
mget *.log              # download หลายไฟล์
mkdir newfolder         # สร้าง folder บน remote
rm file.txt             # ลบไฟล์บน remote
bye                     # ออก
```

### 3.3 ใช้ plink + tar สำหรับ Transfer ไฟล์หลายไฟล์

```powershell
# Download: บีบอัดบน remote แล้ว stream มา local
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "tar czf - /home/sa/transform/" > backup.tar.gz
```

---

## 4. Port Forwarding / Tunneling

### 4.1 Local Port Forwarding

```powershell
# Forward local:5433 → remote:5432 (PostgreSQL)
# เข้าถึง remote PostgreSQL ผ่าน localhost:5433
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" -L 5433:127.0.0.1:5432 -N

# Forward local:8080 → remote:8000 (Web App)
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" -L 8080:127.0.0.1:8000 -N
```

> **Tip:** เพิ่ม `-N` เพื่อไม่เปิด shell (ใช้สำหรับ tunnel อย่างเดียว)

### 4.2 Remote Port Forwarding

```powershell
# ให้ remote เข้าถึง local:3000 ผ่าน remote:9000
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" -R 9000:127.0.0.1:3000 -N
```

### 4.3 Dynamic SOCKS Proxy

```powershell
# สร้าง SOCKS5 proxy ที่ localhost:1080
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" -D 1080 -N
```

---

## 5. การใช้งานกับ Agent (★ วิธีแนะนำ: Persistent Session)

> **หลักการ:** เปิด plink session ค้างไว้ 1 ครั้ง แล้วใช้ `send_command_input` ส่งคำสั่งเข้าไปทีละบรรทัด
> — ไม่ต้องเปิด connection ใหม่ทุกครั้ง → **เร็วกว่า, เสถียรกว่า, หลีกเลี่ยงปัญหา PowerShell escaping**

### 5.1 ขั้นตอนที่ 1 — เปิด Persistent Session

ใช้ `run_command` โดยตั้ง `WaitMsBeforeAsync` ต่ำ (2000ms) เพื่อให้ connection เข้า background:

```json
{
  "tool": "run_command",
  "CommandLine": "plink -ssh sa@ip_addr -P 2233 -pw \"MyP@ssw0rd\"",
  "Cwd": "e:\\NextJS\\my-project",
  "SafeToAutoRun": false,
  "WaitMsBeforeAsync": 2000
}
```

> **สำคัญ:** จดจำ `CommandId` ที่ได้รับ — ต้องใช้ทุกครั้งที่ส่งคำสั่ง

### 5.2 ขั้นตอนที่ 2 — เช็คสถานะ + กด Enter ผ่าน "Access granted"

Plink จะแสดง `"Access granted. Press Return to begin session."` ให้กด Enter:

```json
{
  "tool": "command_status",
  "CommandId": "<command_id_from_step1>",
  "WaitDurationSeconds": 5
}
```

ถ้าเห็น "Access granted" ให้กด Enter:

```json
{
  "tool": "send_command_input",
  "CommandId": "<command_id>",
  "Input": "\n",
  "SafeToAutoRun": true,
  "WaitMs": 2000
}
```

### 5.3 ขั้นตอนที่ 3 — ส่งคำสั่ง Linux ทีละบรรทัด

ใช้ `send_command_input` ส่งคำสั่ง โดย Input ต้องลงท้ายด้วย `\n` (newline):

```json
{
  "tool": "send_command_input",
  "CommandId": "<command_id>",
  "Input": "ls -la /home/sa/transform/\n",
  "SafeToAutoRun": true,
  "WaitMs": 3000
}
```

> **WaitMs Tips:**
>
> - คำสั่งเร็ว (ls, cat, echo): `2000-3000`
> - คำสั่งนาน (python3, docker): `5000-10000`
> - ถ้า output เยอะ: ใช้ `command_status` เพิ่มเติม

### 5.4 ตัวอย่างการใช้งานจริง — Workflow ครบ

```
# ═══════════ Step 1: Login ═══════════
run_command:
  CommandLine: plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd"
  WaitMsBeforeAsync: 2000
  → ได้ CommandId: "abc-123"

# ═══════════ Step 2: กด Enter ═══════════
command_status: CommandId="abc-123", WaitDurationSeconds=5
  → เห็น "Access granted. Press Return..."
send_command_input: CommandId="abc-123", Input="\n", WaitMs=2000
  → เห็น bash prompt "sa@server:~$"

# ═══════════ Step 3: รันคำสั่งต่อเนื่อง ═══════════
send_command_input: Input="uptime\n",                     WaitMs=2000
send_command_input: Input="df -h\n",                       WaitMs=2000
send_command_input: Input="docker ps\n",                   WaitMs=3000
send_command_input: Input="python3 /home/sa/my_script.py\n", WaitMs=8000
send_command_input: Input="cat /var/log/app.log | tail -20\n", WaitMs=3000

# ═══════════ Step 4: สร้างไฟล์บน remote ═══════════
send_command_input: Input="cat << 'EOF' > /home/sa/test.py\nimport os\nprint('hello')\nEOF\n", WaitMs=2000

# ═══════════ Step 5: จบ session (optional) ═══════════
send_command_input: Input="exit\n", WaitMs=1000
```

### 5.5 เปรียบเทียบ: Persistent Session vs One-Shot

|              | Persistent Session (★แนะนำ)           | One-Shot Command                    |
| :----------- | :------------------------------------ | :---------------------------------- |
| **Speed**    | เร็ว — ไม่ต้อง SSH handshake ทุกครั้ง | ช้า — เปิด connection ใหม่ทุกคำสั่ง |
| **Escaping** | ไม่มีปัญหา PowerShell escaping        | ⚠️ ต้องระวัง `"`, `,`, `()`         |
| **Context**  | `cd` ค้างไว้ใช้ต่อได้                 | ทุกคำสั่งเริ่มที่ home              |
| **ใช้เมื่อ** | ต้องรันหลายคำสั่งต่อเนื่อง            | คำสั่งเดียว (เช่น grep, cat)        |

### 5.6 สร้าง/แก้ไขไฟล์บน Remote

```powershell
# วิธีที่ 1: ใช้ cat heredoc ผ่าน send_command_input (ใน persistent session)
cat << 'EOF' > /home/sa/script.py
import os
print("Hello from remote!")
EOF

# วิธีที่ 2: สร้างไฟล์ local แล้ว pscp upload (แนะนำสำหรับไฟล์ใหญ่)
pscp -P 2233 -pw "MyP@ssw0rd" C:\local\script.py sa@ip_addr:/home/sa/

# วิธีที่ 3: ใช้ tee ผ่าน plink (one-shot)
echo "print('hello')" | plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" "tee /home/sa/script.py"
```

> **⚠️ สำหรับไฟล์ยาว:** ให้ใช้ **วิธีที่ 2** (สร้าง local → pscp upload) เสมอ
> เพราะ heredoc ผ่าน plink อาจมีปัญหากับ special characters

---

## 6. Troubleshooting

### 6.1 ปัญหาที่พบบ่อย

| ปัญหา                                              | สาเหตุ                               | แก้ไข                                 |
| :------------------------------------------------- | :----------------------------------- | :------------------------------------ |
| `FATAL ERROR: Network error: Connection timed out` | Host ไม่ตอบ / Firewall block         | เช็ค IP, port, firewall rule          |
| `FATAL ERROR: Network error: Connection refused`   | SSH service ไม่ทำงาน                 | เช็ค `sshd` บน server                 |
| `Access denied`                                    | Password ผิด / User ผิด              | ตรวจสอบ username & password           |
| `Server's host key is not cached`                  | ยังไม่เคย connect                    | ใช้ `echo y \| plink ...`             |
| `Unable to use key file`                           | PPK format ไม่ถูก                    | ใช้ puttygen แปลง key                 |
| `Server refused our key`                           | Public key ไม่อยู่ใน authorized_keys | เพิ่ม key ใน `~/.ssh/authorized_keys` |

### 6.2 Debug Connection

```powershell
# เปิด verbose mode เพื่อดู debug log
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" -v "echo test"
```

### 6.3 เช็ค Port ก่อนเชื่อมต่อ

```powershell
# ทดสอบว่า port เปิดอยู่ไหม
Test-NetConnection -ComputerName ip_addr -Port 2233
```

---

## 7. Best Practices

### 7.1 ความปลอดภัย

```powershell
# ❌ ไม่ดี: password ใน command line (อาจเห็นใน process list)
plink -ssh admin@server -pw "MyP@ssword" "ls"

# ✅ ดีกว่า: ใช้ SSH key
plink -ssh admin@server -i "C:\keys\my_key.ppk" "ls"

# ✅ ดีที่สุด: ใช้ Pageant (PuTTY key agent)
# 1. เปิด Pageant
# 2. เพิ่ม key ใน Pageant
# 3. plink จะใช้ key จาก Pageant อัตโนมัติ
plink -ssh admin@server "ls"
```

### 7.2 Connection Timeout

```powershell
# ตั้ง timeout ป้องกัน hang
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" -batch "ls"

# -batch: ไม่ถาม interactive prompt (auto-reject ถ้ามี prompt)
```

### 7.3 ใช้ Saved Session

```powershell
# 1. สร้าง session ใน PuTTY GUI ชื่อ "my-server"
# 2. ใช้ session name แทนการพิมพ์ทุกอย่าง
plink -load "my-server" "ls -la"
```

### 7.4 Keep-alive ป้องกันหลุด

```powershell
# ส่ง keepalive ทุก 60 วินาที
# ตั้งค่าใน PuTTY GUI: Connection > Seconds between keepalives: 60
# หรือใช้ flag
plink -ssh sa@ip_addr -P 2233 -pw "MyP@ssw0rd" -no-antispoof "ls"
```

---

## Quick Reference

```powershell
# ═══════════ เชื่อมต่อ ═══════════
plink -ssh user@host -P port -pw "pass"                    # interactive shell
plink -ssh user@host -P port -pw "pass" "command"          # one-shot command
plink -ssh user@host -P port -i key.ppk "command"          # SSH key

# ═══════════ รันคำสั่ง ═══════════
plink ... "ls -la"                                          # คำสั่งเดียว
plink ... "cmd1 && cmd2 && cmd3"                            # หลายคำสั่ง
plink ... "cd /path && ./script.sh"                         # cd แล้วรัน
echo "script content" | plink ... "python3 -"               # ส่ง stdin

# ═══════════ ส่งไฟล์ ═══════════
pscp -P port -pw "pass" local.txt user@host:/remote/        # upload
pscp -P port -pw "pass" user@host:/remote/file.txt C:\      # download
pscp -P port -pw "pass" -r C:\folder user@host:/remote/     # upload folder

# ═══════════ Tunnel ═══════════
plink ... -L 5433:127.0.0.1:5432 -N                        # local forward
plink ... -R 9000:127.0.0.1:3000 -N                        # remote forward
plink ... -D 1080 -N                                        # SOCKS proxy

# ═══════════ Troubleshoot ═══════════
plink ... -v "echo test"                                    # verbose debug
Test-NetConnection -ComputerName host -Port port            # test port
echo y | plink ... "echo connected"                         # auto-accept key
```
