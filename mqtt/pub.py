import json
import time
import paho.mqtt.client as mqtt

# ข้อมูลการเชื่อมต่อ Broker (ใช้ IP ภายในเครื่อง Server)
BROKER = "76.13.182.35"
PORT = 1883
TOPIC = "sync/custom"
USER = "hosplk"
PASS = "112233"

# กำหนด Callback เมื่อทำการเชื่อมต่อสำเร็จ
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ Publisher connected to MQTT Broker at {BROKER}:{PORT}")
    else:
        print(f"❌ Failed to connect, return code {rc}")

def main():
    # สร้าง Client instance (รองรับ paho-mqtt 2.0+)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="Python_Publisher")
    client.on_connect = on_connect

    print(f"🔄 Connecting Publisher to {BROKER}...")
    client.username_pw_set(USER, PASS)
    client.connect(BROKER, PORT, 60)
    
    # รันลูปเบื้องหลังเพื่อจัดการเชื่อมต่อ
    client.loop_start()
    
    # รอให้แน่ใจว่าเชื่อมต่อเสร็จแล้ว
    time.sleep(1)

    try:
        source = "sync_dental_monthly"
        sql = """SELECT
    (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode,
    YEAR(i.dchdate) AS discharge_year,
    COUNT(DISTINCT i.an) AS total_admissions,
    COUNT(DISTINCT CASE WHEN i.dchstts = '09' THEN i.an END) AS deaths,
    ROUND(
        COUNT(DISTINCT CASE WHEN i.dchstts = '09' THEN i.an END) * 100.0
        / NULLIF(COUNT(DISTINCT i.an), 0), 2
    ) AS mortality_rate_pct,
    SUM(i.adjrw) AS total_adjrw,
    ROUND(SUM(i.adjrw) / NULLIF(COUNT(DISTINCT i.an), 0), 4) AS cmi,
    NOW() AS d_update
FROM ipt i
INNER JOIN iptdiag d ON d.an = i.an
WHERE
    (d.icd10 LIKE 'I21%' OR d.icd10 LIKE 'I22%'
     OR d.icd10 LIKE 'A40%' OR d.icd10 LIKE 'A41%')
    AND i.dchdate IS NOT NULL
    AND YEAR(i.dchdate) >= 2023
GROUP BY YEAR(i.dchdate)
ORDER BY discharge_year DESC;"""

        payload = json.dumps({
            "source": source,
            "sql": sql
        }, ensure_ascii=False)

        msg = payload
        print(f"📤 Publishing -> Topic: '{TOPIC}', Message: '{msg}'")
        
        # ส่งข้อความ
        client.publish(TOPIC, msg)
        
        # รอให้รับคำสั่งจบ เพื่อให้มั่นใจว่า Publish ถูกส่งออกไปแล้ว
        time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Stopping Publisher...")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Publisher disconnected.")

if __name__ == "__main__":
    main()
