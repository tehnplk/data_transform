import time
import paho.mqtt.client as mqtt

# ข้อมูลการเชื่อมต่อ Broker (ใช้ IP ภายในเครื่อง Server)
BROKER = "192.168.200.242"
PORT = 1883
TOPIC = "test/message"

# กำหนด Callback เมื่อทำการเชื่อมต่อสำเร็จ
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ Subscriber connected to MQTT Broker at {BROKER}:{PORT}")
        # พอเชื่อมต่อสำเร็จปุ๊บ สั่ง Subscribe ในหัวข้อที่สนใจทันที
        print(f"📡 Subscribing to Topic: '{TOPIC}'...")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Failed to connect, return code {rc}")

# กำหนด Callback ฟังก์ชันรอรับข้อความ
def on_message(client, userdata, msg):
    payload_str = msg.payload.decode("utf-8")
    print(f"📩 ----------------------")
    print(f"🎯 Received Message on Topic: [{msg.topic}]")
    print(f"📝 Payload: {payload_str}")
    print(f"------------------------")

def main():
    # สร้าง Client instance (รองรับ paho-mqtt 2.0+)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="Python_Subscriber")
    
    # กำหนด Event Handlers
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"🔄 Connecting Subscriber to {BROKER}...")
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
