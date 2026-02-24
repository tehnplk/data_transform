import time
import paho.mqtt.client as mqtt

# ข้อมูลการเชื่อมต่อ Broker (ใช้ IP ภายในเครื่อง Server)
BROKER = "192.168.200.242"
PORT = 1883
TOPIC = "test/message"

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
    client.connect(BROKER, PORT, 60)
    
    # รันลูปเบื้องหลังเพื่อจัดการเชื่อมต่อ
    client.loop_start()
    
    # รอให้แน่ใจว่าเชื่อมต่อเสร็จแล้ว
    time.sleep(1)

    try:
        count = 1
        while True:
            msg = f"Hello MQTT! This is message number #{count}"
            print(f"📤 Publishing -> Topic: '{TOPIC}', Message: '{msg}'")
            
            # ส่งข้อความ
            client.publish(TOPIC, msg)
            
            count += 1
            time.sleep(2)  # ส่งทุกๆ 2 วินาที

    except KeyboardInterrupt:
        print("\n🛑 Stopping Publisher...")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Publisher disconnected.")

if __name__ == "__main__":
    main()
