import json

vdc_mult_factor= 0.0
adc_div_factor = 1.0
amb_mult_factor = 0.0
amb_div_factor = 1.0


def set_filter_config(configuration):
    global vdc_mult_factor, adc_div_factor,amb_mult_factor, amb_div_factor
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
    
    return True

def doit(reading):
    global vdc_mult_factor, adc_div_factor

    # Extract channel values
    ch1_vdc  = reading.get(b'ANASEN_CH1')
    ch2_adc  = reading.get(b'ANASEN_CH2')
    ch3_amb  = reading.get(b'ANASEN_CH3')

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

# process one or more readings
def calculate_ads_values(readings):
    for elem in list(readings):
        doit(elem['reading'])
    return readings