import json



# Global variable to store limits
LIMITS = {}
MAX_LIMIT_VIOLATION = 10

def set_filter_config(configuration):
    """
    Reads the JSON configuration and stores the necessary values in the LIMITS dictionary.
    """
    global LIMITS
    config = json.loads(configuration["config"])
    
    LIMITS = {
        param: {
            "LOWER_LIMIT": data[0]["LOWER_LIMIT"],
            "UPPER_LIMIT": data[1]["UPPER_LIMIT"]
        }
        for item in config["PARAMETERS"]
        for param, data in item.items()
    }

    return True

def doit(reading):
    """
    Check if sensor readings exceed predefined limits and append limit violation info.
    """
    param_index = 1  # Start indexing from 1
    new_entries = {}  # Store updates separately
    recorded_count = 0  # Track the number of recorded parameters

    reading_c = {k.decode("utf-8") if isinstance(k, bytes) else k: v for k, v in reading.items()}

    for param, value in reading_c.items():
        if param in LIMITS and recorded_count < MAX_LIMIT_VIOLATION:
            lower_limit = LIMITS[param]["LOWER_LIMIT"]
            upper_limit = LIMITS[param]["UPPER_LIMIT"]

            # Determine the limit violation status
            if value > upper_limit:
                violation_status = "UPPER"
                exceeded_limit = upper_limit  # Store upper limit
            elif value < lower_limit:
                violation_status = "LOWER"
                exceeded_limit = lower_limit  # Store lower limit
            else:
                violation_status = "NORMAL"
                exceeded_limit = None  # No limit exceeded


            # Record the parameter and status (even if NORMAL)
            new_entries[bytes(f"Parameter{param_index}", "utf-8")] = param
            new_entries[bytes(f"LimitViolation{param_index}", "utf-8")] = violation_status
            new_entries[f"Value{param_index}".encode("utf-8")] = value
            if exceeded_limit is not None:
                new_entries[f"Limit{param_index}".encode("utf-8")] = exceeded_limit

            
            param_index += 1
            recorded_count += 1  # Increment count

    #Safely update dictionary AFTER iteration
    reading.update(new_entries)


# process one or more readings
def generate_pds_limit_violations(readings):
    for elem in list(readings):
        doit(elem['reading'])
    return readings


#Test the implementation
if __name__ == "__main__":


    config_json = {
        "config": json.dumps({"PARAMETERS": [
      {
        "Voltage_PN1": [
          {
            "LOWER_LIMIT": 5940
          },
          {
            "UPPER_LIMIT": 7260
          }
        ]
      },
      {
        "Voltage_PN2": [
          {
            "LOWER_LIMIT": 5940
          },
          {
            "UPPER_LIMIT": 7260
          }
        ]
      },
      {
        "Voltage_PN3": [
          {
            "LOWER_LIMIT": 5940
          },
          {
            "UPPER_LIMIT": 7260
          }
        ]
      },
      {
        "Current1": [
          {
            "LOWER_LIMIT": -1
          },
          {
            "UPPER_LIMIT": 120
          }
        ]
      },
      {
        "Current2": [
          {
            "LOWER_LIMIT": 0
          },
          {
            "UPPER_LIMIT": 120
          }
        ]
      },
      {
        "Current3": [
          {
            "LOWER_LIMIT": -1
          },
          {
            "UPPER_LIMIT": 120
          }
        ]
      },
      {
        "Frequency1": [
          {
            "LOWER_LIMIT": 49.5
          },
          {
            "UPPER_LIMIT": 50.5
          }
        ]
      },
      {
        "Frequency2": [
          {
            "LOWER_LIMIT": 49.5
          },
          {
            "UPPER_LIMIT": 50.5
          }
        ]
      },
      {
        "Frequency3": [
          {
            "LOWER_LIMIT": 49.5
          },
          {
            "UPPER_LIMIT": 50.5
          }
        ]
      }
    ]
  })
}

    # Set the filter config
    set_filter_config(config_json)

    # Sample readings for testing
    test_readings = [{
           "timestamp":"2025-02-17 04:03:43.531209+00:00",
           "asset":"STMS1_pds_Feeder",
           "reading":{
                     'Voltage_PN1': 5794.37109375, 
                     'Voltage_PN2': 6027.71875, 
                     'Voltage_PN3': 6913.59375, 
                     'Voltage_PP1': 10846.615234375, 
                     'Voltage_PP2': 11790.5556640625, 
                     'Voltage_PP3': 10365.9892578125, 
                     'Current1': 102.2462768555, 
                     'Current2': 101.8574905396, 
                     'Current3': 105.4641189575, 
                     'NeutralCurrent': 6.0272092819, 
                     'Frequency1': 50.2792701721, 
                     'Frequency2': 50.1011123657, 
                     'Frequency3': 49.6276512146
                     }
    
    }]
    
    # Run tests
    generate_pds_limit_violations(test_readings)

