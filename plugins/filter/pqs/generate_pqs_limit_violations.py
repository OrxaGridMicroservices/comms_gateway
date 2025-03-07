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

    # Decode byte keys in `reading`
    reading_c = {k.decode("utf-8") if isinstance(k, bytes) else k: v for k, v in reading.items()}

    # Extract and decode topic safely
    topic = reading_c.get("topic", b"").decode("utf-8") if isinstance(reading_c.get("topic"), bytes) else reading_c.get("topic", "")

    # Check for "pdstop" in topic
    if "pqstop" in topic:

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
              new_entries[bytes(f"Parameter{param_index}", "utf-8")] = bytes(param, "utf-8")
              new_entries[bytes(f"LimitViolation{param_index}", "utf-8")] = bytes(violation_status, "utf-8")
              new_entries[f"Value{param_index}".encode("utf-8")] = value
              if exceeded_limit is not None:
                  new_entries[f"Limit{param_index}".encode("utf-8")] = exceeded_limit


              param_index += 1
              recorded_count += 1  # Increment count

      #Safely update dictionary AFTER iteration
      reading.update(new_entries)


# process one or more readings
def generate_pqs_limit_violations(readings):
    for elem in list(readings):
        doit(elem['reading'])
    return readings


#Test the implementation
if __name__ == "__main__":


   config_json = {
       "config": json.dumps({"PARAMETERS": [
     {
        "MinVtg_R": [
          {
            "LOWER_LIMIT": 80
          },
          {
            "UPPER_LIMIT": 120
          }
        ]
      },
      {
        "MinVtg_Y": [
          {
            "LOWER_LIMIT": 80
          },
          {
            "UPPER_LIMIT": 120
          }
        ]
      },
      {
        "MinVtg_B": [
          {
            "LOWER_LIMIT": 80
          },
          {
            "UPPER_LIMIT": 120
          }
        ]
      },
      {
        "MaxVtg_R": [
          {
            "LOWER_LIMIT": 100
          },
          {
            "UPPER_LIMIT": 200
          }
        ]
      },
      {
        "MaxVtg_Y": [
          {
            "LOWER_LIMIT": 100
          },
          {
            "UPPER_LIMIT": 200
          }
        ]
      },
      {
        "MaxVtg_B": [
          {
            "LOWER_LIMIT": 100
          },
          {
            "UPPER_LIMIT": 200
          }
        ]
      },
      {
        "AvgVtg_R": [
          {
            "LOWER_LIMIT": 90
          },
          {
            "UPPER_LIMIT": 110
          }
        ]
      },
      {
        "AvgVtg_Y": [
          {
            "LOWER_LIMIT": 90
          },
          {
            "UPPER_LIMIT": 110
          }
        ]
      },
      {
        "AvgVtg_B": [
          {
            "LOWER_LIMIT": 90
          },
          {
            "UPPER_LIMIT": 100
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
           "asset":"STMS1_pqs_Feeder",
           "reading":{
                     'MinVtg_R': 13.21, 
                     'MinVtg_Y': 31.31, 
                     'MinVtg_B': 190.08, 
                     'MaxVtg_R': 256.68, 
                     'MaxVtg_Y': 225.87, 
                     'MaxVtg_B': 175.38, 
                     'AvgVtg_R': 134.945, 
                     'AvgVtg_Y': 128.59, 
                     'AvgVtg_B': 182.73
                     }
    
    }]
    
   # Run tests
   generate_pqs_limit_violations(test_readings)

