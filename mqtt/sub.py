import json
import time
import paho.mqtt.client as mqtt

# ข้อมูลการเชื่อมต่อ Broker (ใช้ IP ภายในเครื่อง Server)
BROKER = "76.13.182.35"
PORT = 1883
TOPIC = "sync/custom"
USER = "hosplk"
PASS = "112233"

is_first_connect = True

# กำหนด Callback เมื่อทำการเชื่อมต่อสำเร็จ
def on_connect(client, userdata, flags, rc, properties=None):
    global is_first_connect
    if rc == 0:
        if is_first_connect:
            print(f"✅ Subscriber connected to MQTT Broker at {BROKER}:{PORT}")
            # พอเชื่อมต่อสำเร็จปุ๊บ สั่ง Subscribe ในหัวข้อที่สนใจทันที
            print(f"📡 Subscribing to Topic: '{TOPIC}'...")
            is_first_connect = False
        client.subscribe(TOPIC)
    else:
        print(f"❌ Failed to connect, return code {rc}")

# กำหนด Callback ฟังก์ชันรอรับข้อความ
def on_message(client, userdata, msg):
    payload_str = msg.payload.decode("utf-8")
    print(f"\n📩 ----------------------")
    print(f"🎯 Topic: [{msg.topic}]")
    try:
        data = json.loads(payload_str)
        print(f"📦 Source : {data.get('source', '-')}")
        print(f"📝 SQL    :\n{data.get('sql', payload_str)}")
    except json.JSONDecodeError:
        print(f"📝 Payload: {payload_str}")
    print(f"------------------------")

def main():
    # สร้าง Client instance (รองรับ paho-mqtt 2.0+)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="Python_Subscriber")
    
    # กำหนด Event Handlers
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"🔄 Connecting Subscriber to {BROKER}...")
    client.username_pw_set(USER, PASS)
    client.connect(BROKER, PORT, 60)
    
    try:
        # เปิดลูปค้างไว้ตลอด เพื่อรอรับข้อความ
        print("🕒 Waiting for messages. Press Ctrl+C to exit.")
        client.loop_forever()

    except KeyboardInterrupt:
        print("\n🛑 Stopping Subscriber...")
    finally:
        client.disconnect()
        print("Subscriber disconnected.")

if __name__ == "__main__":
    main()
