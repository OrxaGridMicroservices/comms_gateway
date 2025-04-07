import asyncio
import websockets
import json
import logging
from fledge.common import logger

# Configure logging
_LOGGER = logger.setup(__name__, level=logging.INFO)

def stream_to_websocket(readings):
    """
    Streams readings to a WebSocket server and returns the readings list.

    Args:
        readings (list): List of reading dictionaries.

    Returns:
        list: The original list of readings.
    """
    uri = "ws://ws_server:8000/ws/1/pdstop"  # Replace with your WebSocket server URI
    _LOGGER.info("Establishing WebSocket connection to %s", uri)
    async def send_readings():
        try:
            async with websockets.connect(uri) as websocket:
               for reading in list(readings):
                    # Decode byte-encoded keys and values
                    decoded_reading = convert_bytes_to_str(reading)

                    # Serialize to JSON and send over WebSocket
                    message = json.dumps(decoded_reading)
                    await websocket.send(message)
                    #_LOGGER.info("Sent reading: %s", message)
        except Exception as e:
            _LOGGER.error("An error occurred: %s", e)

    # Create a new event loop and run the asynchronous function within it
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_readings())
    loop.close()

    # Return the original readings to ensure they continue through the Fledge pipeline
    return readings

def convert_bytes_to_str(data):
    """
    Recursively converts byte-encoded keys and values in dictionaries and lists to strings.

    Args:
        data (any): The data to be converted.

    Returns:
        any: The converted data with all byte strings decoded to regular strings.
    """
    if isinstance(data, dict):
        return {convert_bytes_to_str(key): convert_bytes_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_bytes_to_str(element) for element in data]
    elif isinstance(data, bytes):
        return data.decode('utf-8')
    else:
        return data