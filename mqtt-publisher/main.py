import paho.mqtt.client as mqtt
import json
import random
import time
import os

BROKER = os.getenv("BROKER", "localhost")
PORT = int(os.getenv("PORT", 1883))
TOPIC = os.getenv("TOPIC", "sensor/data")
INTERVAL = int(os.getenv("INTERVAL", 5))

# Load configuration from config.json
with open("config.json") as f:
    config = json.load(f)

def generate_payload():
    payload = {
        key: random.uniform(value["min"], value["max"])
        for key, value in config["sensors"].items()
    }
    payload["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    return json.dumps(payload)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}")

client = mqtt.Client("MQTTPublisher", callback_api_version=5)
client.on_connect = on_connect
client.connect(BROKER, PORT, 60)

try:
    while True:
        message = generate_payload()
        result = client.publish(TOPIC, message)
        if result[0] == 0:
            print(f"Published: {message}")
        else:
            print("Failed to publish message.")
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print("Stopping MQTT Publisher.")
    client.disconnect()