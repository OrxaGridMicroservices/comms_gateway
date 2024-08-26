
import time
import json

import uvicorn
import paho.mqtt.client as mqtt
from fastapi import FastAPI
from pydantic import BaseModel


class FlegdeMessage(BaseModel):
    asset: str
    readings: dict
    timestamp: str


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.connect("localhost", 1883, 60)
app = FastAPI()


def handle_fledge_messages(messages):
    """
    asset='sinusoid' readings={'sinusoid': -0.104528463} timestamp='2024-08-26T20:55:03.396870Z'
    """
    print(f'{len(messages)=}')
    # print(f'{messages[0]=}')
    for message in messages:
        # print(message)
        readings_json = json.dumps(message.readings)
        # print(f'{message.asset=}')
        mqttc.publish(f"readings/assets/{message.asset}", readings_json, qos=1)
        mqttc.loop(timeout=1.0)



@app.post("/sensor-reading")
async def sensor_reading(messages: list[FlegdeMessage]):
    handle_fledge_messages(messages)
    # return {"message": "Hello World"}
    # return [_ for _ in messages]
    return {}
"""
  {
    "asset": "randomwalk",
    "readings": {
      "randomwalk": 97
    },
    "timestamp": "2024-08-26T16:37:16.777354Z"
  },
"""


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)



