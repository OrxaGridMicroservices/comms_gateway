import json

# Global variables for configuration values
config_values = {}

def set_filter_config(configuration):
    """
    Reads the JSON configuration and stores the necessary values in global variables.
    """
    global config_values
    config = json.loads(configuration['config'])
    
    # Convert config to a flat dictionary for easier access
    config_values = {k: v for d in config['config'] for k, v in d.items()}

    config_values['ANALOG_CHANNELS'] = config['ANALOG_CHANNELS']

    # Additional handling for OLTC_TAP_CONFIG since it's a list
    config_values['OLTC_TAP_CONFIG'] = [d for d in config['config'] if 'OLTC_TAP_CONFIG' in d][0]['OLTC_TAP_CONFIG']

    return True

def find_tap_position(data, ana_ch, tapsubF):
    """
    Finds the tap position based on the measured value and tap configuration.
    """
    for entry in data:
        tap_measured_value = entry["Measured Value"]
        
        # Calculate the lower and upper bounds
        lower_bound = ana_ch - tapsubF
        upper_bound = ana_ch + tapsubF
        
        # Check if the measured value falls within the range
        if lower_bound < tap_measured_value <= upper_bound:
            return entry["Tap"]
        
    return 0  # Return 0 if no tap position matches

def doit(reading):
    """
    Processes the reading using the global configuration values.
    """
    global config_values
    
    # Example channel mapping (ANALOG_CHANNELS from configuration)
    analog_channels = config_values['ANALOG_CHANNELS']

    for channel in analog_channels:
        channel_key, channel_value = list(channel.items())[1]  # Get the key-value pair for the channel
        reading_key = channel_key.encode()  # Encoding string to bytes for matching reading keys
        
        if reading_key in reading:
             # Skip processing if the channel_value is None
            if channel_value is None:
                continue

            # Normalize the channel value
            normalized_value = channel_value.upper().replace(" ", "_")
            
            # Construct the keys for factors
            mult_key = f"{normalized_value}_MULT_FACTOR"
            div_key = f"{normalized_value}_DIV_FACTOR"
            sub_key = f"{normalized_value}_SUB_FACTOR"
            
            result = reading[reading_key]

            # Apply multiplier factor if it exists
            if mult_key in config_values:
                result *= config_values[mult_key]
            
            # Apply division factor if it exists
            if div_key in config_values:
                result /= config_values[div_key]
            
            # Apply subtraction factor if it exists
            if sub_key in config_values:
                result -= config_values[sub_key]
            
            # Special handling for OLTC: find and store the tap position
            if normalized_value == "OLTC":
                tap_position = find_tap_position(config_values['OLTC_TAP_CONFIG'], reading[reading_key], config_values.get("OLTC_SUB_FACTOR", 0))
                reading[b'TAP_POSITION'] = tap_position
            else:
                # Store the calculated result back in the reading
                reading[normalized_value.encode()] = round(result,2)

# process one or more readings
def calculate_ads_values(readings):
    for elem in list(readings):
        doit(elem['reading'])
    return readings

# Main entry point for testing
if __name__ == "__main__":

    # Example configuration JSON
    config_json = '''
    {
      "_comment": "Channels can be VDC/ADC/Ambient,Oil level/OTI/OLTC",
      "ANALOG_CHANNELS": [
        {"Channel": 1, "ANASEN_CH1": "VDC"},
        {"Channel": 2, "ANASEN_CH2": "ADC"},
        {"Channel": 3, "ANASEN_CH3": "Ambient"},
        {"Channel": 4, "ANASEN_CH4": "OLTC"},
        {"Channel": 5, "ANASEN_CH5": "OIL level"},
        {"Channel": 6, "ANASEN_CH6": "OTI"}
      ],
      "config": [
        {"VDC_MULT_FACTOR": 0.0678},
        {"ADC_DIV_FACTOR": 297.9},
        {"ADC_SUB_FACTOR": 0},
        {"AMBIENT_MULT_FACTOR": 195},
        {"AMBIENT_DIV_FACTOR": 3000},
        {"OIL_LEVEL_MULT_FACTOR": 1},
        {"OIL_LEVEL_DIV_FACTOR": 1},
        {"OTI_MULT_FACTOR": 1},
        {"OTI_DIV_FACTOR": 1},
        {"WTI_MULT_FACTOR": 1},
        {"WIL_DIV_FACTOR": 1},
        {"OLTC_SUB_FACTOR": 100},
        {
          "OLTC_TAP_CONFIG": [
            {"Tap": 1, "Measured Value": 100, "Expected Value": 34650},
            {"Tap": 2, "Measured Value": 260, "Expected Value": 34237},
            {"Tap": 3, "Measured Value": 406, "Expected Value": 33825},
            {"Tap": 4, "Measured Value": 545, "Expected Value": 33412},
            {"Tap": 5, "Measured Value": 686, "Expected Value": 33000},
            {"Tap": 6, "Measured Value": 825, "Expected Value": 32587},
            {"Tap": 7, "Measured Value": 990, "Expected Value": 32175},
            {"Tap": 8, "Measured Value": 1145, "Expected Value": 31762},
            {"Tap": 9, "Measured Value": 1248, "Expected Value": 31350},
            {"Tap": 10, "Measured Value": 1389, "Expected Value": 30937}
          ]
        }
      ]
    }
    '''
    
    # Example reading
    reading = {
        b'ANASEN_CH1': 1185.0,
        b'ANASEN_CH2': 729.0,
        b'ANASEN_CH3': 1503.0,
        b'ANASEN_CH4': 1.0,
        b'ANASEN_CH5': 1200.0,
        b'ANASEN_CH6': 1400.0,
        b'timestamp': '2025-01-07 16:17:21',
        b'IsNlf': 0
    }
    
    
    # Load the configuration
    set_filter_config(config_json)
    # Process the reading
    updated_reading = doit(reading)
    print(updated_reading)
