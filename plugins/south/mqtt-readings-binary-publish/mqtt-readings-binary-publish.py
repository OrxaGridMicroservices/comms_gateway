import asyncio
import copy
import uvicorn
from fastapi import FastAPI
from fastapi_mqtt import FastMQTT, MQTTConfig
from pydantic import BaseModel
from contextlib import asynccontextmanager
import logging
from fledge.common import logger
from fledge.plugins.common import utils
from fledge.services.south import exceptions
from fledge.services.south.ingest import Ingest

__author__ = "Sanjeev Kumar"
__copyright__ = "Copyright (c) 2025 OrxaGrid, Ltd."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_LOGGER = logger.setup(__name__, level=logging.DEBUG)

c_callback = None
c_ingest_ref = None
loop = None
_uvicorn_started = False

config=""
app = FastAPI()  #Declare FastAPI app
fast_mqtt = None  #Placeholder; will be set later
topic = ""

_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'MQTT publisher South Plugin',
        'type': 'string',
        'default': 'mqtt-readings-binary-publish',
        'readonly': 'true'
    },
    'brokerHost': {
        'description': 'Hostname or IP address of the broker to connect to',
        'type': 'string',
        'default': 'localhost',
        'order': '1',
        'displayName': 'MQTT Broker host',
        'mandatory': 'true'
    },
    'brokerPort': {
        'description': 'The network port of the broker to connect to',
        'type': 'integer',
        'default': '1883',
        'order': '2',
        'displayName': 'MQTT Broker Port',
        'mandatory': 'true'
    },
    'username': {
        'description': 'Username for broker authentication',
        'type': 'string',
        'default': '',
        'order': '3',
        'displayName': 'Username'
    },
    'password': {
        'description': 'Password for broker authentication',
        'type': 'password',
        'default': '',
        'order': '4',
        'displayName': 'Password'
    },
    'keepAliveInterval': {
        'description': 'Maximum period in seconds allowed between communications with the broker. If no other messages are being exchanged, '
                        'this controls the rate at which the client will send ping messages to the broker.',
        'type': 'integer',
        'default': '60',
        'order': '5',
        'displayName': 'Keep Alive Interval'
    },
    'topic': {
        'description': 'The subscription topic to subscribe to receive messages',
        'type': 'string',
        'default': 'Room1/conditions',
        'order': '6',
        'displayName': 'Topic To Subscribe',
        'mandatory': 'true'
    },
    'qos': {
        'description': 'The desired quality of service level for the subscription',
        'type': 'integer',
        'default': '0',
        'order': '7',
        'displayName': 'QoS Level',
        'minimum': '0',
        'maximum': '2'
    }
}


def plugin_info():
    return {
        'name': 'MQTT Publisher',
        'version': '1.0.0',
        'mode': 'async',
        'type': 'south',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }

def plugin_init(data):
    global config, fast_mqtt, topic

    config = data
    _LOGGER.info("Initializing MQTT Plugin with config: %s", config)

    topic = config['topic']['value']

    mqtt_config = MQTTConfig(
        host=config["brokerHost"]["value"],
        port=int(config["brokerPort"]["value"]),
        keepalive=int(config["keepAliveInterval"]["value"]),
        username=config.get("username", {}).get("value"),
        password=config.get("password", {}).get("value")
    )

    # Initialize FastMQTT after config is built
    fast_mqtt = FastMQTT(config=mqtt_config)
    fast_mqtt.init_app(app)

    return config

def plugin_start(handle):
    global _uvicorn_started
    if not _uvicorn_started:
        _LOGGER.info("Launching FastAPI server on port 8082...")
        start_fastapi_server()
        _uvicorn_started = True

def plugin_shutdown(handle):
    _LOGGER.info("Shutting down MQTT Plugin...")

def plugin_register_ingest(handle, callback, user_data):
    _LOGGER.info("Registering ingest callback function...")

def plugin_reconfigure(handle, new_config):
    """ Reconfigures the plugin

    it should be called when the configuration of the plugin is changed during the operation of the South service;
    The new configuration category should be passed.

    Args:
        handle: handle returned by the plugin initialisation call
        new_config: JSON object representing the new configuration category for the category
    Returns:
        new_handle: new handle to be used in the future calls
    Raises:
    """
    _LOGGER.info('Reconfiguring MQTT south plugin...')
    plugin_shutdown(handle)

    new_handle = plugin_init(new_config)
    plugin_start(new_handle)

    _LOGGER.info('MQTT south plugin reconfigured.')
    return new_handle

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure MQTT runs in the same event loop as FastAPI
    loop = asyncio.get_event_loop()
    task = loop.create_task(fast_mqtt.connection())  # Start MQTT connection
    yield
    await fast_mqtt.disconnect()  # Disconnect MQTT when shutting down

app = FastAPI(lifespan=lifespan)

# Pydantic model for publishing messages
class PayloadRequest(BaseModel):
    payload_hex: str

# **POST API to publish MQTT messages**
@app.post("/api/DigiOps/Publish")
async def publish_message(payload: PayloadRequest):
    try:
        _LOGGER.info("Received API request for publishing DigiOps: %s", payload.payload_hex)
        fast_mqtt.publish(topic, bytes.fromhex(payload.payload_hex))
        return {
            "status": "Message Published",
            "topic": topic,
            "hex_payload": payload.payload_hex
        }
    except Exception as e:
        return {"error": str(e)}

async def start_uvicorn():
    """Runs Uvicorn inside the existing event loop."""
    _LOGGER.info("Inside start_uvicorn()")
    config = uvicorn.Config(app, host="0.0.0.0", port=8082, log_level="debug")
    server = uvicorn.Server(config)
    await server.serve()

def start_fastapi_server():
    """Start Uvicorn inside a new event loop running in a separate thread."""
    _LOGGER.info("Starting FastAPI server thread with new event loop")

    def _runner():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_uvicorn())
        except Exception as e:
            _LOGGER.error(f"Failed to run Uvicorn server: {e}", exc_info=True)

    import threading
    t = threading.Thread(target=_runner, name="UvicornThread", daemon=True)
    t.start()
    _LOGGER.info("FastAPI thread started")