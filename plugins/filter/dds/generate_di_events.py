import json
import requests

# 🔹 Global dictionary for storing configuration
config_values = {}

# 🔹 Dictionary for storing previous DI values
previous_values = {}

# 🔹 Base URL for fetching previous state
FLEDGE_BASE_URL = "http://fledge-api:8000"  # Update with actual URL

def fetch_previous_values(asset):
    """
    Fetches the last known DI values from the Fledge API.
    """
    global previous_values
    url = f"{FLEDGE_BASE_URL}/comm_gw/fledge/asset/{asset}?limit=1&skip=0&previous=false"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                previous_values=data[0]["reading"] # Update previous state with last known values
                #print(previous_values)
    except requests.RequestException as e:
        print(f"Error fetching previous values: {e}")
        
    return True

def set_filter_config(configuration):
    """
    Reads the JSON configuration and stores the necessary values in global variables.
    """
    global config_values
    config = json.loads(configuration['config'])  
    
    config_values['DIGITAL_CHANNELS'] = config['DIGITAL_CHANNELS']

     # Store only non-null digital channels
    config_values['DIGITAL_CHANNEL_NAME'] = {
        list(d.keys())[0]: list(d.values())[0] for d in config['DIGITAL_CHANNEL_NAME'] if list(d.values())[0] is not None
    }

    # Store only channels that have valid names
    config_values['DIGITAL_CHANNEL_TYPE'] = {
        list(d.keys())[0]: list(d.values())[0] for d in config['DIGITAL_CHANNEL_TYPE'] if list(d.keys())[0] in config_values['DIGITAL_CHANNEL_NAME']
    }

    # Store channel states for SP1 and DP1
    config_values['DIGITAL_CHANNEL_STATE'] = {
        list(d.keys())[0]: {int(list(state.keys())[0]): list(state.values())[0] for state in list(d.values())[0]}
        for d in config['DIGITAL_CHANNEL_STATE']
    }
    
    return True
  
def doit(reading, asset):
    """
    Processes the digital input readings and generates events when values change.
    """
    
    global previous_values
    
    # Decode byte keys in `reading`
    reading_c = {k.decode("utf-8") if isinstance(k, bytes) else k: v for k, v in reading.items()}

    # Extract and decode topic safely
    topic = reading_c.get("topic", b"").decode("utf-8") if isinstance(reading_c.get("topic"), bytes) else reading_c.get("topic", "")

    # Check for "ddstop" in topic
    if "ddstop" in topic:
   
        if "Digi1" not in previous_values:
            fetch_previous_values(asset)  # Fetch previous values if not already stored
            
        events = []
        processed_dp1 = set()  # Track DP1 channels to prevent duplicate events

        for channel in config_values['DIGITAL_CHANNELS']:
            channel_id = f"Digi{channel['Channel']}"
            
            # Skip if channel is not configured with a valid name
            if channel_id not in config_values['DIGITAL_CHANNEL_NAME']:
                continue  

            channel_name = config_values['DIGITAL_CHANNEL_NAME'][channel_id]
            channel_type = config_values['DIGITAL_CHANNEL_TYPE'].get(channel_id, "SP1")
            no_of_bits = 1  # Default SP1 to 1 bit

            new_value = reading_c.get(channel_id, 0)
            prev_value = previous_values.get(channel_id, 0)

            if channel_type == "DP1":  # Handling DP1 event
                if channel_id in processed_dp1:
                    continue  # Skip if already processed

                second_channel_id = f"Digi{channel['Channel'] + 1}"
                dp1_value = (new_value, reading_c.get(second_channel_id, 0))
                int_value = dp1_value[0] * 1 + dp1_value[1] * 2  # Convert (0,1) to integer 1

                state_name = config_values['DIGITAL_CHANNEL_STATE']['DP1'].get(int_value, "UNKNOWN")
                no_of_bits = 2  # DP1 uses 2 bits

                # Ensure DP1 is stored in the correct event slot (Digi1 position)
                event_channel = channel_id
                di_value_str = f"{dp1_value[0]}, {dp1_value[1]}"

                # Mark DP1 channels as processed
                processed_dp1.add(channel_id)
                processed_dp1.add(second_channel_id)
                
                prev_value = previous_values.get(channel_id, 0) * 1  + previous_values.get(second_channel_id, 0) * 2

            else:  # SP1 (Single Point)
                state_name = config_values['DIGITAL_CHANNEL_STATE']['SP1'].get(new_value, "UNKNOWN")
                int_value = new_value
                event_channel = channel_id
                di_value_str = str(new_value)

            # Generate event only if value changed
            if int_value != prev_value:
                event = {
                    "name": channel_name,
                    "channel": event_channel,
                    "di_value": int_value,
                    "state": state_name,
                    "No_of_bits": no_of_bits
                }
                events.append((channel['Channel'], event))  # Store event with channel position
                
        # Sort events by channel position before storing in `reading`
        events.sort(key=lambda x: x[0])  

        if events:
            print("Generated Events:", [e[1] for e in events])

        for channel_pos, event in events:
            for key, value in event.items():
                reading[bytes(f"{key}{channel_pos}", "utf-8")] = value  # Correct: Uses `channel_pos`
        # Update previous values
        previous_values = reading_c.copy()
    
def generate_di_events(readings):
    """
    Wrapper function that processes readings and generates DI events.
    """
    for reading in list(readings):
        asset = reading.get("asset_code", b"").decode("utf-8")
        doit(reading['reading'],asset)
    return readings

# 🔹 Test the implementation
if __name__ == "__main__":
    config_json = {
        "config": json.dumps({
            "DIGITAL_CHANNELS": [
                {"Channel": 1, "Field": "Digi1"},
                {"Channel": 2, "Field": "Digi2"},
                {"Channel": 3, "Field": "Digi3"},
                {"Channel": 4, "Field": "Digi4"},
                {"Channel": 5, "Field": "Digi5"},
                {"Channel": 6, "Field": "Digi6"},
                {"Channel": 7, "Field": "Digi7"},
                {"Channel": 8, "Field": "Digi8"}
            ],
            "DIGITAL_CHANNEL_NAME": [
                {"Digi1": "CB"},
                {"Digi2": "CB"},
                {"Digi3": "OC"},
                {"Digi4": "EF"},
                {"Digi5": None},
                {"Digi6": None},
                {"Digi7": None},
                {"Digi8": None}
            ],
            "DIGITAL_CHANNEL_TYPE": [
                {"Digi1": "DP1"},
                {"Digi2": "DP1"},
                {"Digi3": "SP1"},
                {"Digi4": "SP1"},
                {"Digi5": None},
                {"Digi6": None},
                {"Digi7": None},
                {"Digi8": None}
            ],
            "DIGITAL_CHANNEL_STATE": [
                {"DP1": [
                    {"0": "INVALID"},
                    {"1": "OPEN"},
                    {"2": "CLOSE"},
                    {"3": "INTERMEDIATE"}
                ]},
                {"SP1": [
                    {"0": "OPEN"},
                    {"1": "CLOSE"}
                ]}
            ]
        })
    }
    
    asset='STMS1_dds_Feeder'

    set_filter_config(config_json)

    test_readings = [
        {
            "timestamp": "2025-02-07 07:21:34.826479+00:00",
            "asset": "STMS1_dds_Feeder_ph7",
            "reading": {
                "Digi1": 0,
                "Digi2": 1,
                "Digi3": 0,
                "Digi4": 0,
                "Digi5": 1,
                "Digi6": 0,
                "Digi7": 0,
                "Digi8": 0,
                "timestamp": "2025-02-07 12:51:34",
                "IsNlf": 0,
                "topic": "STMS1/ddstop"
            }
        }
    ]

    generate_di_events(test_readings)
    
    events =[{'name': 'OC',
      'channel': 'Digi3',
      'di_value': 0,
      'state': 'OPEN',
      'No_of_bits': 1},
     {'name': 'EF',
      'channel': 'Digi4',
      'di_value': 0,
      'state': 'OPEN',
      'No_of_bits': 1}]
    
    reading = {
    'Digi1': 0,
    'Digi2': 1,
    'Digi3': 0,
    'Digi4': 0,
    'Digi5': 1,
    'Digi6': 0,
    'Digi7': 0,
    'Digi8': 0,
    'timestamp': '2025-02-07 12:51:34',
    'IsNlf': 0,
    'topic': 'STMS1/ddstop'
}

    # Insert event details into reading with byte-string keys
    for i, event in enumerate(events, start=1):
        for key, value in event.items():
            reading[bytes(f"{key}{i}", "utf-8")] = value  # Only keys are bytes, values remain as normal
    
    # Print updated reading
    print(reading)