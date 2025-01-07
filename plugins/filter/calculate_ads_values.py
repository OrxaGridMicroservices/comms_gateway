import json

vdc_mult_factor= 0.0
adc_div_factor = 1.0
amb_mult_factor = 0.0
amb_div_factor = 1.0
oltc_sub_factor = 0.0
oltc_tap_config = []


def set_filter_config(configuration):
    global vdc_mult_factor, adc_div_factor,amb_mult_factor, amb_div_factor, oltc_sub_factor,oltc_tap_config
    config = json.loads(configuration['config'])
    
    #Get VDC mult factor
    if ('VDC_MULT_FACTOR' in config):
        vdc_mult_factor = config['VDC_MULT_FACTOR']
   
    #Get ADC Div factor
    if ('ADC_DIV_FACTOR' in config):
        adc_div_factor = config['ADC_DIV_FACTOR']

    #Get AMB mult factor
    if ('AMBIENT_MULT_FACTOR' in config):
        amb_mult_factor = config['AMBIENT_MULT_FACTOR']

    #Get AMB div factor
    if ('AMBIENT_DIV_FACTOR' in config):
        amb_div_factor = config['AMBIENT_DIV_FACTOR']

    #Get OLTC Sub factor
    if ('OLTC_SUB_FACTOR' in config):
        oltc_sub_factor = config['OLTC_SUB_FACTOR']
    
     #Get OLTC Tap Configuration
    if ('OLTC_TAP_CONFIG' in config):
        oltc_tap_config = config.get("OLTC_TAP_CONFIG", [])
    
    return True

def find_tap_position(data,ana_ch,tapsubF):
    for entry in data:
        tap_measured_value = entry["Measured Value"]
        
        # Calculate the lower and upper bounds
        lower_bound = ana_ch - tapsubF
        upper_bound = ana_ch + tapsubF
        
        # Check if the measured value falls within the range
        if lower_bound < tap_measured_value <= upper_bound:
            return entry["Tap"]
        
    return None  # Return None if no tap position match
    

def doit(reading):
    global vdc_mult_factor, adc_div_factor,amb_mult_factor, amb_div_factor, oltc_sub_factor, oltc_tap_config

    # Extract channel values
    ch1_vdc  = reading.get(b'ANASEN_CH1')
    ch2_adc  = reading.get(b'ANASEN_CH2')
    ch3_amb  = reading.get(b'ANASEN_CH3')
    ch4_oltc = reading.get(b'ANASEN_CH4')

    #Calculate battery Voltage
    if ch1_vdc is not None:
        vdc = ch1_vdc * vdc_mult_factor
        reading[b'Battery_VDC'] = vdc

    #Calculate battery Voltage
    if ch2_adc is not None:
        adc = round(ch2_adc/adc_div_factor,2)
        reading[b'Battery_ADC'] = adc

    #Calculate Ambient temperature
    if ch3_amb is not None:
        amb = round(ch3_amb * amb_mult_factor/amb_div_factor,2)
        reading[b'AmbientTemp'] = amb

    #Calculate Tap position 
    if ch4_oltc is not None:
        reading[b'TapPosition'] = find_tap_position(oltc_tap_config,ch4_oltc,oltc_sub_factor)
    

# process one or more readings
def calculate_ads_values(readings):
    for elem in list(readings):
        doit(elem['reading'])
    return readings