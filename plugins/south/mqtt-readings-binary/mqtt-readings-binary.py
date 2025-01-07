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
    auth
        a dict containing authentication parameters for the client:
        
        auth = {‘username’:”<username>”, ‘password’:”<password>”}

        Defaults to None, which indicates no authentication is to be used.
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
import uuid

import paho.mqtt.client as mqtt

from fledge.common import logger
from fledge.plugins.common import utils
from fledge.services.south import exceptions
from fledge.services.south.ingest import Ingest
import async_ingest
import struct

__author__ = "Praveen Garg"
__copyright__ = "Copyright (c) 2020 Dianomic Systems, Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_LOGGER = logger.setup(__name__, level=logging.INFO)

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
    'keepAliveInterval': {
        'description': 'Maximum period in seconds allowed between communications with the broker. If no other messages are being exchanged, '
                        'this controls the rate at which the client will send ping messages to the broker.',
        'type': 'integer',
        'default': '60',
        'order': '3',
        'displayName': 'Keep Alive Interval'
    },
    'topic': {
        'description': 'The subscription topic to subscribe to receive messages',
        'type': 'string',
        'default': 'Room1/conditions',
        'order': '4',
        'displayName': 'Topic To Subscribe',
        'mandatory': 'true'
    },
    'qos': {
        'description': 'The desired quality of service level for the subscription',
        'type': 'integer',
        'default': '0',
        'order': '5',
        'displayName': 'QoS Level',
        'minimum': '0',
        'maximum': '2'
    },
    'assetName': {
        'description': 'Name of Asset',
        'type': 'string',
        'default': 'mqtt-',
        'order': '6',
        'displayName': 'Asset Name',
        'mandatory': 'true'
    }
}


def plugin_info():
    return {
        'name': 'MQTT Subscriber',
        'version': '1.9.2',
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

    __slots__ = ['mqtt_client', 'broker_host', 'broker_port', 'topic', 'qos', 'keep_alive_interval', 'asset', 'loop']

    def __init__(self, config):
        self.mqtt_client = mqtt.Client()
        self.broker_host = config['brokerHost']['value']
        self.broker_port = int(config['brokerPort']['value'])
        self.topic = config['topic']['value']
        self.qos = int(config['qos']['value'])
        self.keep_alive_interval = int(config['keepAliveInterval']['value'])
        self.asset = config['assetName']['value']

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
        if "adstop" in str(msg.topic):
          self.loop.run_until_complete(self.save_ads(msg))
        
        #Save PDS data
        if "pdstop" in str(msg.topic):
            self.loop.run_until_complete(self.save_pds(msg))

        #Save DDS data
        if "ddstop" in str(msg.topic):
            self.loop.run_until_complete(self.save_dds(msg))
        
        #Save PQ data
        if "pqstop" in str(msg.topic):
            self.loop.run_until_complete(self.save_pq(msg))

    def on_subscribe(self, client, userdata, mid, granted_qos):
        pass

    def on_unsubscribe(self, client, userdata, mid):
        pass

    def start(self):
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

    async def save_ads(self, msg):
        """Store msg content to Fledge with support for binary and JSON payloads."""
        try:
            struct_format = (
                '<'     # Little-endian specifier
                '4f'    # 4 floats for AnalogData
                'B B B B B B H'  # Timestamp components: seconds, minutes, hours, weekday, date, month, year
                '?'     # Boolean for IsNlf
            )
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


    async def save_pds(self, msg):
        """Store msg content to Fledge with support for binary and JSON payloads."""
        try:
            struct_format = (
                '<'  # Little-endian specifier
                '3f 3f 3f f 3f 3f f 3f 3f 3f f f f f f f f f f f f f f f 3f 3f 3f '
                'f f f f f f f f f f f f f f f f f f f f f f f f f f f f f 3f 3f '
                '3f f f f 3f 3f 3f f f f f B B B B B B H ?'
            )

           
            #PDS parameters
            field_names = [
                "Voltage_PN1", "Voltage_PN2", "Voltage_PN3",
                "Voltage_PP1", "Voltage_PP2", "Voltage_PP3",
                "Current1", "Current2", "Current3",
                "NeutralCurrent", "Frequency1", "Frequency2", "Frequency3",
                "PowerFactor1", "PowerFactor2", "PowerFactor3",
                "AveragePF", "ActivePower1", "ActivePower2", "ActivePower3",
                "ReactivePower1", "ReactivePower2", "ReactivePower3",
                "ApparentPower1", "ApparentPower2", "ApparentPower3",
                "TotalActivePower", "TotalReactivePower", "TotalApparentPower",
                "AngleVA_VB", "AngleVB_VC", "AngleVA_VC",
                "AngleVA_IA", "AngleVB_IB", "AngleVC_IC",
                "AngleIA_IB", "AngleIB_IC", "AngleIA_IC",
                "ActiveEnergy1", "ActiveEnergy2", "ActiveEnergy3",
                "ReactiveEnergy1", "ReactiveEnergy2", "ReactiveEnergy3",
                "ApparentEnergy1", "ApparentEnergy2", "ApparentEnergy3",
                "Accum_ActEnergy", "Accum_ReactEnergy", "Accum_ApprntEnergy",
                "Total_ActEnergy", "Total_ReactEnergy", "Total_ApprntEnergy",
                "ActImpEnergy_R", "ActExpEnergy_R", "ActImpEnergy_Y", "ActExpEnergy_Y",
                "ActImpEnergy_B", "ActExpEnergy_B", "ReactEnergy_R_Q1", "ReactEnergy_R_Q2",
                "ReactEnergy_R_Q3", "ReactEnergy_R_Q4", "ReactEnergy_Y_Q1", "ReactEnergy_Y_Q2",
                "ReactEnergy_Y_Q3", "ReactEnergy_Y_Q4", "ReactEnergy_B_Q1", "ReactEnergy_B_Q2",
                "ReactEnergy_B_Q3", "ReactEnergy_B_Q4", "ReactImpEnergy_R", "ReactExpEnergy_R",
                "ReactImpEnergy_Y", "ReactExpEnergy_Y", "ReactImpEnergy_B", "ReactExpEnergy_B",
                "AppExpEnergy_R", "AppExpEnergy_Y", "AppExpEnergy_B",
                "ActImpCumEnergy", "ActExpCumEnergy", "AppImpEnergy_R", "AppImpEnergy_Y",
                "AppImpEnergy_B", "AppImpcumEnergy", "AppExpcumEnergy",
                "ReactiveCumQ1", "ReactiveCumQ2", "ReactiveCumQ3", "ReactiveCumQ4",
                "VTHD1", "VTHD2", "VTHD3", "ITHD1", "ITHD2", "ITHD3",
                "seconds", "minutes", "hours", "weekday", "date", "month", "year", "IsNlf"
            ]

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

    async def save_dds(self, msg):
        """Store msg content to Fledge with support for binary and JSON payloads."""
        try:
            struct_format = (
                '<'     # Little-endian specifier
                '8B'    # 8 bytes for digital data (DigitalData)
                'B B B B B B H'  # Timestamp components: seconds, minutes, hours, weekday, date, month, year
                '?'     # Boolean for IsNlf
            )
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

    async def save_pq(self, msg):
        """Store msg content to Fledge with support for binary and JSON payloads."""
        try:
            struct_format = (
                '<'                  # Little-endian specifier
                '3f3f3f'             # minVtg[3], maxVtg[3], avgVtg[3]
                '3f3f3f'             # minCur[3], maxCur[3], avgCur[3]
                '3f3f3f'             # minFreq[3], maxFreq[3], avgFreq[3]
                'HHHfHHHfHHHf'       # Dip[3 phases]: 3 integers + 1 float per phase
                'HHHfHHHfHHHf'       # Swell[3 phases]: 3 integers + 1 float per phase
                'HHHfHHHfHHHf'       # Intrp
                'HffHffHff'          # RVC[3 phases]: 3 integers + 1 float per phase'
                '3f3f3f3f'           # crestFactor[3], overCurrent[3], underVoltage[3], overVoltage[3]
                '6f2f6f2f'           # symmCompVtg, unbCompVtg, symmCompCur, unbCompCur
                '3f3f'               # vtgTHD[3], curTHD[3]
                '6f'                 # UOD[3]
                'H3fH3fH3f'          # flicker
                '6f'                 # MSVValues[3]
                'I'                  # eventRegister
                'B B B B B B H'      # t_Timestamp
                '?'                  # IsNlf
            )

            #PQ parameters
            field_names = [
                "MinVtg_R", "MinVtg_Y", "MinVtg_B", 
                "MaxVtg_R", "MaxVtg_Y", "MaxVtg_B", 
                "AvgVtg_R", "AvgVtg_Y", "AvgVtg_B", 
                "MinCur_R", "MinCur_Y", "MinCur_B", 
                "MaxCur_R", "MaxCur_Y", "MaxCur_B", 
                "AvgCur_R", "AvgCur_Y", "AvgCur_B", 
                "MinFreq_R", "MinFreq_Y", "MinFreq_B", 
                "MaxFreq_R", "MaxFreq_Y", "MaxFreq_B", 
                "AvgFreq_R", "AvgFreq_Y", "AvgFreq_B", 
                "Dip_InstCount_R", "Dip_InstCount_Y", "Dip_InstCount_B", 
                "Dip_ResVoltage_R", "Dip_ResVoltage_Y", "Dip_ResVoltage_B", 
                "Dip_MomntCount_R", "Dip_MomntCount_Y", "Dip_MomntCount_B", 
                "Dip_TempCount_R", "Dip_TempCount_Y", "Dip_TempCount_B", 
                "Swell_InstCount_R", "Swell_InstCount_Y", "Swell_InstCount_B",
                "Swell_ResVoltage_R", "Swell_ResVoltage_Y", "Swell_ResVoltage_B", 
                "Swell_MomntCount_R", "Swell_MomntCount_Y", "Swell_MomntCount_B", 
                "Swell_TempCount_R", "Swell_TempCount_Y", "Swell_TempCount_B", 
                "Intrp_InstCount_R", "Intrp_InstCount_Y", "Intrp_InstCount_B", 
                "Intrp_ResVoltage_R", "Intrp_ResVoltage_Y", "Intrp_ResVoltage_B", 
                "Intrp_MomntCount_R", "Intrp_MomntCount_Y", "Intrp_MomntCount_B",
                "Intrp_TempCount_R", "Intrp_TempCount_Y", "Intrp_TempCount_B", 
                "Rvc_Count_R", "Rvc_Count_Y", "Rvc_Count_B", 
                "Rvc_DeltaUss_R", "Rvc_DeltaUss_Y", "Rvc_DeltaUss_B", 
                "Rvc_DeltaUmax_R", "Rvc_DeltaUmax_Y", "Rvc_DeltaUmax_B", 
                "CrestFactor_R", "CrestFactor_Y", "CrestFactor_B", 
                "OverCurrent_R", "OverCurrent_Y", "OverCurrent_B", 
                "UnderVoltage_R", "UnderVoltage_Y", "UnderVoltage_B", 
                "OverVoltage_R", "OverVoltage_Y", "OverVoltage_B", 
                "SymCompVtg_NegSeqAng", "SymCompVtg_PosSeqAng", "SymCompVtg_PosSeqMag", 
                "SymCompVtg_NegSeqMag", "SymCompVtg_ZeroSeqAng", "SymCompVtg_ZeroSeqMag", 
                "UnbCompVtg_NegUnbPct", "UnbCompVtg_ZeroUnbPct", "SymCompCur_NegSeqAng", 
                "SymCompCur_PosSeqAng", "SymCompCur_PosSeqMag", "SymCompCur_NegSeqMag", 
                "SymCompCur_ZeroSeqAng", "SymCompCur_ZeroSeqMag", 
                "UnbCompCur_NegUnbPct", "UnbCompCur_ZeroUnbPct",
                "VtgTHD_R", "VtgTHD_Y", "VtgTHD_B", 
                "CurTHD_R", "CurTHD_Y", "CurTHD_B", 
                "Uod_R_OverDeviation", "Uod_R_UnderDeviation", "Uod_Y_OverDeviation", 
                "Uod_Y_UnderDeviation", "Uod_B_OverDeviation", "Uod_B_UnderDeviation", 
                "Flicker_FlickInst_Event", "Flicker_FlickInst_Level_R", "Flicker_FlickInst_Level_Y", 
                "Flicker_FlickInst_Level_B", "Flicker_FlickShort_Event", "Flicker_FlickShort_Level_R", 
                "Flicker_FlickShort_Level_Y", "Flicker_FlickShort_Level_B", "Flicker_FlickLong_Event", 
                "Flicker_FlickLong_Level_R", "Flicker_FlickLong_Level_Y", "Flicker_FlickLong_Level_B", 
                "EventRegister", "IsNlf"
            ]

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

