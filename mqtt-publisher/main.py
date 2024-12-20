import paho.mqtt.client as mqtt
import json
import random
import time
import os

BROKER = os.getenv("BROKER", "localhost")
PORT = int(os.getenv("PORT", 1883))
INTERVAL = int(os.getenv("INTERVAL", 5))
MQTT_DEVICE = os.getenv("MQTT_DEVICE", "device1,device2").split(",")

# Load configuration from config.json
try:
    with open("config.json") as f:
        config = json.load(f)
except FileNotFoundError:
    print("Error: config.json not found!")
    exit(1)

def generate_payload(device_name):
    payload = {
        key: random.uniform(value["min"], value["max"])
        for key, value in config["sensors"].items()
    }
    payload.update({
        "device": device_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    return json.dumps(payload)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.connect(BROKER, PORT, 60)

try:
    while True:
        for device in MQTT_DEVICE:
            topic = f"{device}/data"
            message = generate_payload(device)
            result = client.publish(topic, message)
            if result[0] == 0:
                print(f"Published to {topic}: {message}")
            else:
                print(f"Failed to publish message to {topic}.")
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print("Stopping MQTT Publisher.")
    client.disconnect()