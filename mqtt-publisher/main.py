import json
import os
import random
import time
from datetime import datetime
from threading import Thread
import paho.mqtt.client as mqtt

# Load configuration files
PDS_CONFIG = json.load(open("config_pds.json"))
ADS_CONFIG = json.load(open("config_ads.json"))
DDS_CONFIG = json.load(open("config_dds.json"))

# Configuration for MQTT topics and intervals
MQTT_DEVICE = os.getenv("MQTT_DEVICE", "device1,device2").split(",")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
PDS_INTERVAL = int(os.getenv("PDS_INTERVAL", 60))  # Default 1 minute
ADS_INTERVAL = int(os.getenv("ADS_INTERVAL", 10))  # Default 10 seconds

# Initialize MQTT client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}")

client.on_connect = on_connect
client.connect(MQTT_BROKER, MQTT_PORT)
client.loop_start()

def get_current_timestamp():
    """Returns the current UTC time in the format YYYY-MM-DD HH:MM:SS."""
    return time.strftime("%Y-%m-%d %H:%M:%S")

def generate_pds_payload():
    payload = {}
    for sensor, limits in PDS_CONFIG["sensors"].items():
        payload[sensor] = round(random.uniform(limits["min"], limits["max"]), 4)
    payload["timestamp"] =  get_current_timestamp()
    return payload

def generate_ads_payload():
    payload = {}
    for sensor, limits in ADS_CONFIG["sensors"].items():
        payload[sensor] = round(random.uniform(limits["min"], limits["max"]), 2)
    payload["timestamp"] =  get_current_timestamp()
    return payload

def generate_dds_payload():
    payload = {}
    current_time =  get_current_timestamp()
    for channel, data in DDS_CONFIG["channels"].items():
        previous_state = data["state"]
        new_state = random.choice([0, 1])  # Simulate state change
        if new_state != previous_state:
            DDS_CONFIG["channels"][channel]["state"] = new_state
            payload[channel] = {"state": new_state, "timestamp": current_time}
    return payload

def publish_pds():
    while True:
      for device in MQTT_DEVICE:
        topic = f"{device}/pdsdata"
        payload = generate_pds_payload()
        client.publish(topic, json.dumps(payload))
        print(f"Published PDS data to {topic}: {payload}")
      time.sleep(PDS_INTERVAL)

def publish_ads():
    while True:
      for device in MQTT_DEVICE:
        topic = f"{device}/adsdata"
        payload = generate_ads_payload()
        client.publish(topic, json.dumps(payload))
        print(f"Published ADS data to {topic}: {payload}")
      time.sleep(ADS_INTERVAL)

def publish_dds():
    while True:
     for device in MQTT_DEVICE:
        topic = f"{device}/ddsdata"
        payload = generate_dds_payload()
        if payload:  # Publish only if there's a state change
            client.publish(topic, json.dumps(payload))
            print(f"Published DDS data to {topic}: {payload}")
     time.sleep(10)  # Check DDS state changes frequently

# Run tasks in separate threads
try:
    threads = [
        Thread(target=publish_pds, daemon=True),
        Thread(target=publish_ads, daemon=True),
        Thread(target=publish_dds, daemon=True)
    ]

    for thread in threads:
        thread.start()

    # Keep the main thread alive
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Stopping MQTT Publisher.")
    client.loop_stop()
    client.disconnect()