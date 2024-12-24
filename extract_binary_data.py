def doit(reading):
    raise Exception(f"{reading}")

# process one or more readings
def extract_binary_data(readings):
    for elem in list(readings):
        doit(elem['reading'])
    return readings