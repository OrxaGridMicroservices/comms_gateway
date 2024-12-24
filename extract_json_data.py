def doit(reading):
    # Extract voltage and current values
    voltage = reading.get(b'r_RMSVoltage')

    if voltage is not None:
        temp = voltage * 2

        # Store the calculated power in the reading
        reading[b'temp'] = temp

# process one or more readings
def extract_json_data(readings):
    for elem in list(readings):
        doit(elem['reading'])
    return readings