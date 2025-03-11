# -*- coding: utf-8 -*-

# FLEDGE_BEGIN
# See: http://fledge-iot.readthedocs.io/
# FLEDGE_END

""" WebSocket North Plugin """

import asyncio
import json
import logging
import base64
import websockets
import numpy as np

from fledge.common import logger
from fledge.plugins.north.common.common import *

__author__ = "Sanjeev Kumar"
__copyright__ = "Copyright (c) 2017 OrxaGrid, Ltd"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_LOGGER = logger.setup(__name__, level=logging.INFO)

ws_north = None
config = ""

_CONFIG_CATEGORY_NAME = "WS"
_CONFIG_CATEGORY_DESCRIPTION = "WebSocket North Plugin"

_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'WebSocket North Plugin',
        'type': 'string',
        'default': 'ws_north',
        'readonly': 'true'
    },
    'url': {
        'description': 'WebSocket Server URL',
        'type': 'string',
        'default': 'ws://localhost:8760',
        'order': '1',
        'displayName': 'WebSocket URL'
    },
    "source": {
        "description": "Source of data to be sent on the stream. May be either readings or statistics.",
        "type": "enumeration",
        "default": "readings",
        "options": ["readings", "statistics"],
        'order': '2',
        'displayName': 'Source'
    },
    "verifySSL": {
        "description": "Verify SSL certificate",
        "type": "boolean",
        "default": "false",
        'order': '3',
        'displayName': 'Verify SSL'
    }
}


def plugin_info():
    return {
        'name': 'ws',
        'version': '1.0',
        'type': 'north',
        'mode': 'async',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(data):
    global ws_north, config
    ws_north = WebSocketNorthPlugin()
    config = data
    return config


async def plugin_send(data, payload, stream_id):
    try:
        is_data_sent, new_last_object_id, num_sent = await ws_north.send_payloads(payload)
    except asyncio.CancelledError:
        pass
    else:
        return is_data_sent, new_last_object_id, num_sent


def plugin_shutdown(data):
    pass


def plugin_reconfigure():
    pass


class NumpyEncoderBase64(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            obj_data = np.ascontiguousarray(obj).data
            data_list = base64.b64encode(obj_data)
            if isinstance(data_list, bytes):
                data_list = data_list.decode(encoding='UTF-8')
            return {
                "__ndarray__": data_list,
                "dtype": str(obj.dtype),
                "shape": obj.shape
            }
        super(NumpyEncoderBase64, self).default(obj)


class WebSocketNorthPlugin:
    """ WebSocket North Plugin """

    def __init__(self):
        self.event_loop = asyncio.get_event_loop()

    async def send_payloads(self, payloads):
        is_data_sent = False
        last_object_id = 0
        num_sent = 0
        try:
            payload_block = []
            for p in payloads:
                last_object_id = p["id"]
                read = {
                    "asset": p["asset_code"],
                    "readings": p["reading"],
                    "timestamp": p["user_ts"]
                }
                for k, v in read["readings"].items():
                    if isinstance(v, np.ndarray):
                        read["readings"][k] = json.dumps(v, cls=NumpyEncoderBase64)
                payload_block.append(read)

            num_sent = await self._send_payloads(payload_block)
            is_data_sent = True
        except Exception as ex:
            _LOGGER.exception("Data could not be sent: %s", str(ex))

        return is_data_sent, last_object_id, num_sent

    async def _send_payloads(self, payload_block):
        """Send a list of payloads over WebSocket"""
        num_count = 0
        url = config['url']['value']

        try:
            async with websockets.connect(url) as websocket:
                await websocket.send(json.dumps(payload_block))
                response = await websocket.recv()
                num_count += len(payload_block)
                _LOGGER.info("Received response: %s", num_count)
        except Exception as e:
            _LOGGER.error("Failed to send WebSocket data: %s", str(e))

        return num_count