# -*- coding: utf-8 -*-

# FLEDGE_BEGIN
# See: http://fledge-iot.readthedocs.io/
# FLEDGE_END

""" MQTT Subscriber 

TODO:

# MQTT v5 support using paho-mqtt v1.5.0 
    https://github.com/eclipse/paho.mqtt.python/blob/master/ChangeLog.txt

# broker bind_address
    The IP address of a local network interface to bind this client to, assuming multiple interfaces exist

# Subscriber
    topics
        This can either be a string or a list of strings if multiple topics should be subscribed to.
    msg_count
        the number of messages to retrieve from the broker. Defaults to 1. If >1, a list of MQTTMessages will be returned.
    retained
        set to True to consider retained messages, set to False to ignore messages with the retained flag set.
    client_id
        the MQTT client id to use. If “” or None, the Paho library will generate a client id automatically.
    will
        a dict containing will parameters for the client:
        
        will = {‘topic’: “<topic>”, ‘payload’:”<payload”>, ‘qos’:<qos>, ‘retain’:<retain>}.
        Topic is required, all other parameters are optional and will default to None, 0 and False respectively.

        Defaults to None, which indicates no will should be used.
    tls
        a dict containing TLS configuration parameters for the cient:

        dict = {‘ca_certs’:”<ca_certs>”, ‘certfile’:”<certfile>”, ‘keyfile’:”<keyfile>”, ‘tls_version’:”<tls_version>”, ‘ciphers’:”<ciphers”>}

        ca_certs is required, all other parameters are optional and will default to None if not provided, which results in the client using the default behaviour - see the paho.mqtt.client documentation.

        Defaults to None, which indicates that TLS should not be used.

    protocol
        choose the version of the MQTT protocol to use. Use either MQTTv31 or MQTTv311. 
"""

import asyncio
import copy
import json
import logging

import paho.mqtt.client as mqtt

from fledge.common import logger
from fledge.plugins.common import utils
from fledge.services.south import exceptions
from fledge.services.south.ingest import Ingest
import async_ingest
import struct

__author__ = "Praveen Garg, Oskar Gert"
__copyright__ = "Copyright (c) 2024 Dianomic Systems, Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_LOGGER = logger.setup(__name__, level=logging.WARNING)

c_callback = None
c_ingest_ref = None
loop = None

_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'MQTT Subscriber South Plugin',
        'type': 'string',
        'default': 'mqtt-readings-binary',
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
    },
    'assetName': {
        'description': 'Name of Asset',
        'type': 'string',
        'default': 'mqtt-',
        'order': '8',
        'displayName': 'Asset Name',
        'mandatory': 'true',
        'group': 'Reading'
    },
    'reading_datapoint_name_for_primitive_value': {
        'description': 'Datapoint name to be used in the reading object only for a primitive value, published to the topic',
        'type': 'string',
        'default': 'datapoint',
        'order': '9',
        'displayName': 'Datapoint Name',
        'group': 'Reading'
    }
}


def plugin_info():
    return {
        'name': 'MQTT Subscriber',
        'version': '2.6.0',
        'mode': 'async',
        'type': 'south',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(config):
    """Registers MQTT Subscriber Client

    Args:
        config: JSON configuration document for the South plugin configuration category
    Returns:
        handle: JSON object to be used in future calls to the plugin
    Raises:
    """
    handle = copy.deepcopy(config)
    handle["_mqtt"] = MqttSubscriberClient(handle)
    return handle


def plugin_start(handle):
    global loop
    loop = asyncio.new_event_loop()

    _LOGGER.info('Starting MQTT south plugin...')
    try:
        _mqtt = handle["_mqtt"]
        _mqtt.loop = loop
        _mqtt.start()
    except Exception as e:
        _LOGGER.exception(str(e))
    else:
        _LOGGER.info('MQTT south plugin started.')

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


def plugin_shutdown(handle):
    """ Shut down the plugin

    To be called prior to the South service being shut down.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
    Raises:
    """
    global loop
    try:
        _LOGGER.info('Shutting down MQTT south plugin...')
        _mqtt = handle["_mqtt"]
        _mqtt.stop()
        
        loop.stop()
        loop = None
    except Exception as e:
        _LOGGER.exception(str(e))
    else:
        _LOGGER.info('MQTT south plugin shut down.')


def plugin_register_ingest(handle, callback, ingest_ref):
    """ Required plugin interface component to communicate to South C server
    Args:
        handle: handle returned by the plugin initialisation call
        callback: C opaque object required to passed back to C->ingest method
        ingest_ref: C opaque object required to passed back to C->ingest method
    """
    global c_callback, c_ingest_ref
    c_callback = callback
    c_ingest_ref = ingest_ref


class MqttSubscriberClient(object):
    """ mqtt listener class"""

    __slots__ = ['mqtt_client', 'broker_host', 'broker_port', 'username', 'password', 'topic', 'qos', 'keep_alive_interval', 'asset', 'reading_datapoint_name_for_primitive_value', 'loop']

    def __init__(self, config):
        self.mqtt_client = mqtt.Client()
        self.broker_host = config['brokerHost']['value']
        self.broker_port = int(config['brokerPort']['value'])
        self.username = config['username']['value']
        self.password = config['password']['value']
        self.topic = config['topic']['value']
        self.qos = int(config['qos']['value'])
        self.keep_alive_interval = int(config['keepAliveInterval']['value'])
        
        self.asset = config['assetName']['value']
        self.reading_datapoint_name_for_primitive_value = config['reading_datapoint_name_for_primitive_value']['value']

    def on_connect(self, client, userdata, flags, rc):
        """ The callback for when the client receives a CONNACK response from the server
        """
        client.connected_flag = True
        # subscribe at given Topic on connect
        client.subscribe(self.topic, self.qos)
        _LOGGER.info("MQTT connected. Subscribed the topic: %s", self.topic)

    def on_disconnect(self, client, userdata, rc):
        pass

    def on_message(self, client, userdata, msg):
        """ The callback for when a PUBLISH message is received from the server
        """
        _LOGGER.info("MQTT Received message; Topic: %s, Payload: %s  with QoS: %s", str(msg.topic), str(msg.payload),
                     str(msg.qos))

        #Save ADS data
        if "adstop" in str(msg.topic) and "ph8" in str(msg.topic):
          self.loop.run_until_complete(self.save_ads_ph8(msg))
        elif "adstop" in str(msg.topic):
          self.loop.run_until_complete(self.save_ads_ph7(msg))

        #Save PDS data
        if "pdstop" in str(msg.topic) and "ph8" in str(msg.topic):
            self.loop.run_until_complete(self.save_pds_ph8(msg))
        elif "pdstop" in str(msg.topic):
          self.loop.run_until_complete(self.save_pds_ph7(msg))

        #Save DDS data
        if "ddstop" in str(msg.topic) and "ph8" in str(msg.topic):
            self.loop.run_until_complete(self.save_dds_ph8(msg))
        elif "ddstop" in str(msg.topic):
          self.loop.run_until_complete(self.save_dds_ph7(msg))
        
        #Save PQ data
        if "pqstop" in str(msg.topic) and "ph8" in str(msg.topic):
            self.loop.run_until_complete(self.save_pq_ph8(msg))
        elif "pqstop" in str(msg.topic):
          self.loop.run_until_complete(self.save_pq_ph7(msg))

    def on_subscribe(self, client, userdata, mid, granted_qos):
        pass

    def on_unsubscribe(self, client, userdata, mid):
        pass

    def start(self):
        if self.username and len(self.username.strip()) and self.password and len(self.password):
            # no strip on pwd len check, as it can be all spaces?!
            self.mqtt_client.username_pw_set(self.username, password=self.password)
        # event callbacks
        self.mqtt_client.on_connect = self.on_connect

        self.mqtt_client.on_subscribe = self.on_subscribe
        self.mqtt_client.on_message = self.on_message

        self.mqtt_client.on_disconnect = self.on_disconnect

        self.mqtt_client.connect(self.broker_host, self.broker_port, self.keep_alive_interval)
        _LOGGER.info("MQTT connecting..., Broker Host: %s, Port: %s", self.broker_host, self.broker_port)

        self.mqtt_client.loop_start()

    def stop(self):
        self.mqtt_client.disconnect()
        self.mqtt_client.loop_stop()

    def convert(self, msg):
        constructors = [json.loads, int, float, str]
        for constructor in constructors:
            try:
                # Only convert if type is string
                converted_msg = constructor(msg) if type(msg) == str else msg
                # Create dict if converted msg isn't already a dict
                if not isinstance(converted_msg, dict):
                    converted_msg = {self.reading_datapoint_name_for_primitive_value: converted_msg}
            except (ValueError, TypeError) as error:
                pass
            else:
               return converted_msg
        _LOGGER.exception("Unable to convert payload '%s' to a suitable type", str(msg)) 
        
    async def save_ads_ph7(self, msg):
        """Store msg content to Fledge with support for binary and JSON payloads."""
        try:
            
            # Read the data back from the JSON file
            with open('/usr/local/fledge/python/fledge/plugins/south/mqtt-readings-binary/ads.json', 'r') as json_file:
                ads_data = json.load(json_file)

            # Access the struct_format and field_names
            struct_format = ads_data['struct_format']
            field_names = ads_data['field_names']

            struct_size = struct.calcsize(struct_format)

            # Ensure payload size matches struct size
            if len(msg.payload) != struct_size:
                raise ValueError(f"Payload size {len(msg.payload)} does not match expected size {struct_size}.")

            # Unpack the payload
            unpacked_data = struct.unpack(struct_format, msg.payload)

            # Extract data
            analog_data = unpacked_data[:4]
            timestamp = unpacked_data[4:11]  # seconds, minutes, hours, weekday, date, month, year
            is_nlf = unpacked_data[11]

            # Handle year correctly
            year = timestamp[6] if timestamp[6] > 99 else 2000 + timestamp[6]

            # Format timestamp
            formatted_timestamp = f"{year}-{timestamp[5]:02d}-{timestamp[4]:02d} {timestamp[2]:02d}:{timestamp[1]:02d}:{timestamp[0]:02d}"

            # Build the JSON object
            payload_data = {
                "ANASEN_CH1": analog_data[0],
                "ANASEN_CH2": analog_data[1],
                "ANASEN_CH3": analog_data[2],
                "ANASEN_CH4": analog_data[3],
                "timestamp": formatted_timestamp,
                "IsNlf": is_nlf,
                "topic": str(msg.topic)
            }
        except:
                # If decoding fails, treat it as binary data
            payload_data = {
                'binary_data': list(msg.payload)  # Convert binary payload to a list of integers
            }
        
        # Prepare data for ingestion
        _LOGGER.debug("Ingesting data on topic %s: %s", str(msg.topic), payload_data)
        data = {
            'asset': self.asset,
            'timestamp': utils.local_timestamp(),
            'readings': payload_data
        }
        
        # Use async_ingest callback to save data
        await async_ingest.ingest_callback(c_callback, c_ingest_ref, data)

    async def save_ads_ph8(self, msg):
        """Store msg content to Fledge with support for binary and JSON payloads."""
        try:
            
            # Read the data back from the JSON file
            with open('/usr/local/fledge/python/fledge/plugins/south/mqtt-readings-binary/ads_ph8.json', 'r') as json_file:
                ads_data = json.load(json_file)

            # Access the struct_format and field_names
            struct_format = ads_data['struct_format']
            field_names = ads_data['field_names']

            struct_size = struct.calcsize(struct_format)

            # Ensure payload size matches struct size
            if len(msg.payload) != struct_size:
                raise ValueError(f"Payload size {len(msg.payload)} does not match expected size {struct_size}.")

            # Unpack the payload
            unpacked_data = struct.unpack(struct_format, msg.payload)

            # Extract data
            analog_data = unpacked_data[:6]
            timestamp = unpacked_data[6:13]  # seconds, minutes, hours, weekday, date, month, year
            is_nlf = unpacked_data[13]

            # Handle year correctly
            year = timestamp[6] if timestamp[6] > 99 else 2000 + timestamp[6]

            # Format timestamp
            formatted_timestamp = f"{year}-{timestamp[5]:02d}-{timestamp[4]:02d} {timestamp[2]:02d}:{timestamp[1]:02d}:{timestamp[0]:02d}"

            # Build the JSON object
            payload_data = {
                "ANASEN_CH1": analog_data[0],
                "ANASEN_CH2": analog_data[1],
                "ANASEN_CH3": analog_data[2],
                "ANASEN_CH4": analog_data[3],
                "ANASEN_CH5": analog_data[4],
                "ANASEN_CH6": analog_data[5],
                "timestamp": formatted_timestamp,
                "IsNlf": is_nlf,
                "topic": str(msg.topic)
            }
        except:
                # If decoding fails, treat it as binary data
            payload_data = {
                'binary_data': list(msg.payload)  # Convert binary payload to a list of integers
            }
        
        # Prepare data for ingestion
        _LOGGER.debug("Ingesting data on topic %s: %s", str(msg.topic), payload_data)
        data = {
            'asset': self.asset,
            'timestamp': utils.local_timestamp(),
            'readings': payload_data
        }
        
        # Use async_ingest callback to save data
        await async_ingest.ingest_callback(c_callback, c_ingest_ref, data)



    async def save_pds_ph7(self, msg):
        """Store msg content to Fledge with support for binary and JSON payloads."""
        try:
            # Read the data back from the JSON file
            with open('/usr/local/fledge/python/fledge/plugins/south/mqtt-readings-binary/pds.json', 'r') as json_file:
                pds_data = json.load(json_file)

            # Access the struct_format and field_names
            struct_format = pds_data['struct_format']
            field_names = pds_data['field_names']
            #Calculate struct size
            struct_size = struct.calcsize(struct_format)

            # Ensure payload size matches struct size
            if len(msg.payload) != struct_size:
                raise ValueError(f"Payload size {len(msg.payload)} does not match expected size {struct_size}.")


            #Unpack the payload
            unpacked_data = struct.unpack(struct_format, msg.payload)
            
            #convert into json payload
            json_payload = {field_name: value for field_name, value in zip(field_names, unpacked_data)}

           # Parse and format timestamp
            timestamp_data = unpacked_data[-8:-1]
            seconds, minutes, hours, weekday, date, month, year = timestamp_data
            year = int(year) if year > 99 else 2000 + int(year)
            formatted_timestamp = f"{year}-{int(month):02d}-{int(date):02d} {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            json_payload["timestamp"] = formatted_timestamp
            
            # Convert IsNlf to boolean
            json_payload["IsNlf"] = bool(unpacked_data[-1])

            # send topic type
            json_payload["topic"] = str(msg.topic)

            #Assign to payload_data
            payload_data = json_payload

        except:
                # If decoding fails, treat it as binary data
            payload_data = {
                'binary_data': list(msg.payload)  # Convert binary payload to a list of integers
            }
        
        # Prepare data for ingestion
        _LOGGER.debug("Ingesting data on topic %s: %s", str(msg.topic), payload_data)
        data = {
            'asset': self.asset,
            'timestamp': utils.local_timestamp(),
            'readings': payload_data
        }
        
        # Use async_ingest callback to save data
        await async_ingest.ingest_callback(c_callback, c_ingest_ref, data)

    async def save_pds_ph8(self, msg):
        """Store msg content to Fledge with support for binary and JSON payloads."""
        try:
            # Read the data back from the JSON file
            with open('/usr/local/fledge/python/fledge/plugins/south/mqtt-readings-binary/pds_ph8.json', 'r') as json_file:
                pds_data = json.load(json_file)

            # Access the struct_format and field_names
            struct_format = pds_data['struct_format']
            field_names = pds_data['field_names']
            #Calculate struct size
            struct_size = struct.calcsize(struct_format)

            # Ensure payload size matches struct size
            if len(msg.payload) != struct_size:
                raise ValueError(f"Payload size {len(msg.payload)} does not match expected size {struct_size}.")


            #Unpack the payload
            unpacked_data = struct.unpack(struct_format, msg.payload)
            
            #convert into json payload
            json_payload = {field_name: value for field_name, value in zip(field_names, unpacked_data)}

           # Parse and format timestamp
            timestamp_data = unpacked_data[-8:-1]
            seconds, minutes, hours, weekday, date, month, year = timestamp_data
            year = int(year) if year > 99 else 2000 + int(year)
            formatted_timestamp = f"{year}-{int(month):02d}-{int(date):02d} {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            json_payload["timestamp"] = formatted_timestamp
            
            # Convert IsNlf to boolean
            json_payload["IsNlf"] = bool(unpacked_data[-1])

            # send topic type
            json_payload["topic"] = str(msg.topic)

            #Assign to payload_data
            payload_data = json_payload

        except:
                # If decoding fails, treat it as binary data
            payload_data = {
                'binary_data': list(msg.payload)  # Convert binary payload to a list of integers
            }
        
        # Prepare data for ingestion
        _LOGGER.debug("Ingesting data on topic %s: %s", str(msg.topic), payload_data)
        data = {
            'asset': self.asset,
            'timestamp': utils.local_timestamp(),
            'readings': payload_data
        }
        
        # Use async_ingest callback to save data
        await async_ingest.ingest_callback(c_callback, c_ingest_ref, data)

    async def save_dds_ph7(self, msg):
        """Store msg content to Fledge with support for binary and JSON payloads."""
        try:

            with open('/usr/local/fledge/python/fledge/plugins/south/mqtt-readings-binary/dds.json', 'r') as json_file:
                dds_data = json.load(json_file)

            # Access the struct_format and field_names
            struct_format = dds_data['struct_format']
            field_names = dds_data['field_names']

            struct_size = struct.calcsize(struct_format)

            # Ensure payload size matches struct size
            if len(msg.payload) != struct_size:
                raise ValueError(f"Payload size {len(msg.payload)} does not match expected size {struct_size}.")

            # Unpack the payload
            unpacked_data = struct.unpack(struct_format, msg.payload)

            # Extract data
            digital_data = unpacked_data[:8]
            timestamp = unpacked_data[8:15]  # seconds, minutes, hours, weekday, date, month, year
            is_nlf = unpacked_data[15]

            # Handle year correctly
            year = timestamp[6] if timestamp[6] > 99 else 2000 + timestamp[6]

            # Format timestamp
            formatted_timestamp = f"{year}-{timestamp[5]:02d}-{timestamp[4]:02d} {timestamp[2]:02d}:{timestamp[1]:02d}:{timestamp[0]:02d}"

            # Build the JSON object
            payload_data = {
            "Digi1": digital_data[0],
            "Digi2": digital_data[1],
            "Digi3": digital_data[2],
            "Digi4": digital_data[3],
            "Digi5": digital_data[4],
            "Digi6": digital_data[5],
            "Digi7": digital_data[6],
            "Digi8": digital_data[7],
            "timestamp": formatted_timestamp,
            "IsNlf": is_nlf,
            "topic": str(msg.topic)
            }
        except:
                # If decoding fails, treat it as binary data
            payload_data = {
                'binary_data': list(msg.payload)  # Convert binary payload to a list of integers
            }
        
        # Prepare data for ingestion
        _LOGGER.debug("Ingesting data on topic %s: %s", str(msg.topic), payload_data)
        data = {
            'asset': self.asset,
            'timestamp': utils.local_timestamp(),
            'readings': payload_data
        }
        
        # Use async_ingest callback to save data
        await async_ingest.ingest_callback(c_callback, c_ingest_ref, data)

    async def save_dds_ph8(self, msg):
        """Store msg content to Fledge with support for binary and JSON payloads."""
        try:

            with open('/usr/local/fledge/python/fledge/plugins/south/mqtt-readings-binary/dds_ph8.json', 'r') as json_file:
                dds_data = json.load(json_file)

            # Access the struct_format and field_names
            struct_format = dds_data['struct_format']
            field_names = dds_data['field_names']

            struct_size = struct.calcsize(struct_format)

            # Ensure payload size matches struct size
            if len(msg.payload) != struct_size:
                raise ValueError(f"Payload size {len(msg.payload)} does not match expected size {struct_size}.")

            # Unpack the payload
            unpacked_data = struct.unpack(struct_format, msg.payload)

            # Extract data
            digital_data = unpacked_data[:22]
            timestamp = unpacked_data[22:29]  # seconds, minutes, hours, weekday, date, month, year
            is_nlf = unpacked_data[29]

            # Handle year correctly
            year = timestamp[6] if timestamp[6] > 99 else 2000 + timestamp[6]

            # Format timestamp
            formatted_timestamp = f"{year}-{timestamp[5]:02d}-{timestamp[4]:02d} {timestamp[2]:02d}:{timestamp[1]:02d}:{timestamp[0]:02d}"

            # Build the JSON object
            payload_data = {
            "Digi1": digital_data[0],
            "Digi2": digital_data[1],
            "Digi3": digital_data[2],
            "Digi4": digital_data[3],
            "Digi5": digital_data[4],
            "Digi6": digital_data[5],
            "Digi7": digital_data[6],
            "Digi8": digital_data[7],
            "Digi9": digital_data[8],
            "Digi10": digital_data[9],
            "Digi11": digital_data[10],
            "Digi12": digital_data[11],
            "Digi13": digital_data[12],
            "Digi14": digital_data[13],
            "Digi15": digital_data[14],
            "Digi16": digital_data[15],
            "Digi17": digital_data[16],
            "Digi18": digital_data[17],
            "Digi19": digital_data[18],
            "Digi20": digital_data[19],
            "Digi21": digital_data[20],
            "Digi22": digital_data[21],
            "timestamp": formatted_timestamp,
            "IsNlf": is_nlf,
            "topic": str(msg.topic)
            }
        except:
                # If decoding fails, treat it as binary data
            payload_data = {
                'binary_data': list(msg.payload)  # Convert binary payload to a list of integers
            }
        
        # Prepare data for ingestion
        _LOGGER.debug("Ingesting data on topic %s: %s", str(msg.topic), payload_data)
        data = {
            'asset': self.asset,
            'timestamp': utils.local_timestamp(),
            'readings': payload_data
        }
        
        # Use async_ingest callback to save data
        await async_ingest.ingest_callback(c_callback, c_ingest_ref, data)

    async def save_pq_ph7(self, msg):
        """Store msg content to Fledge with support for binary and JSON payloads."""
        try:
            # Read the data back from the JSON file
            with open('/usr/local/fledge/python/fledge/plugins/south/mqtt-readings-binary/pqs.json', 'r') as json_file:
                pqs_data = json.load(json_file)

            # Access the struct_format and field_names
            struct_format = pqs_data ['struct_format']
            field_names = pqs_data ['field_names']

            #Calculate struct size
            struct_size = struct.calcsize(struct_format)

            # Ensure payload size matches struct size
            if len(msg.payload) != struct_size:
                raise ValueError(f"Payload size {len(msg.payload)} does not match expected size {struct_size}.")


            #Unpack the payload
            unpacked_data = struct.unpack(struct_format, msg.payload)
            
            #convert into json payload
            json_payload = {field_name: value for field_name, value in zip(field_names, unpacked_data)}

           # Parse and format timestamp
            timestamp_data = unpacked_data[-8:-1]
            seconds, minutes, hours, weekday, date, month, year = timestamp_data
            year = int(year) if year > 99 else 2000 + int(year)
            formatted_timestamp = f"{year}-{int(month):02d}-{int(date):02d} {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            json_payload["timestamp"] = formatted_timestamp
            
            # Convert IsNlf to boolean
            json_payload["IsNlf"] = bool(unpacked_data[-1])

             # send topic type
            json_payload["topic"] = str(msg.topic)

            #Assign to payload_data
            payload_data = json_payload

        except:
                # If decoding fails, treat it as binary data
            payload_data = {
                'binary_data': list(msg.payload)  # Convert binary payload to a list of integers
            }
        
        # Prepare data for ingestion
        _LOGGER.debug("Ingesting PQ data on topic %s: %s", str(msg.topic), payload_data)
        data = {
            'asset': self.asset,
            'timestamp': utils.local_timestamp(),
            'readings': payload_data
        }
        
        # Use async_ingest callback to save data
        await async_ingest.ingest_callback(c_callback, c_ingest_ref, data)

    async def save_pq_ph8(self, msg):
        """Store msg content to Fledge with support for binary and JSON payloads."""
        try:
            # Read the data back from the JSON file
            with open('/usr/local/fledge/python/fledge/plugins/south/mqtt-readings-binary/pqs_ph8.json', 'r') as json_file:
                pqs_data = json.load(json_file)

            # Access the struct_format and field_names
            struct_format = pqs_data ['struct_format']
            field_names = pqs_data ['field_names']

            #Calculate struct size
            struct_size = struct.calcsize(struct_format)

            # Ensure payload size matches struct size
            if len(msg.payload) != struct_size:
                raise ValueError(f"Payload size {len(msg.payload)} does not match expected size {struct_size}.")


            #Unpack the payload
            unpacked_data = struct.unpack(struct_format, msg.payload)
            
            #convert into json payload
            json_payload = {field_name: value for field_name, value in zip(field_names, unpacked_data)}

           # Parse and format timestamp
            timestamp_data = unpacked_data[-8:-1]
            seconds, minutes, hours, weekday, date, month, year = timestamp_data
            year = int(year) if year > 99 else 2000 + int(year)
            formatted_timestamp = f"{year}-{int(month):02d}-{int(date):02d} {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            json_payload["timestamp"] = formatted_timestamp
            
            # Convert IsNlf to boolean
            json_payload["IsNlf"] = bool(unpacked_data[-1])

             # send topic type
            json_payload["topic"] = str(msg.topic)

            #Assign to payload_data
            payload_data = json_payload

        except:
                # If decoding fails, treat it as binary data
            payload_data = {
                'binary_data': list(msg.payload)  # Convert binary payload to a list of integers
            }
        
        # Prepare data for ingestion
        _LOGGER.debug("Ingesting PQ data on topic %s: %s", str(msg.topic), payload_data)
        data = {
            'asset': self.asset,
            'timestamp': utils.local_timestamp(),
            'readings': payload_data
        }
        
        # Use async_ingest callback to save data
        await async_ingest.ingest_callback(c_callback, c_ingest_ref, data)
