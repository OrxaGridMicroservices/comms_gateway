#!/bin/bash

# Wait for Fledge to be ready
echo "Waiting for Fledge to be online..."
until curl -s -o /dev/null -w '%{http_code}' http://comms_gw:8081/fledge/ping | grep -q '200'; do
  echo "Still waiting for Fledge..."
  sleep 2
done

echo "Fledge is online. Proceeding with north plugin configuration..."

echo "create the MQTT_publish south plugin."

curl --location 'http://comms_gw:8081/fledge/service' \
--header 'Accept: application/json, text/plain, */*' \
--data '{"name":"MQTT_PUBLISH","type":"south","plugin":"mqtt-readings-binary-publish","config":{"brokerHost":{"value":"emqx"},"username":{"value":"mqtt_user_1"},"password":{"value":"ba0d8613-8ad2-427a-b9d7-00fb5e8f2f01"},"topic":{"value":"#/dostop"}},"enabled":true}'

echo "Create the HTTP North plugin"

curl -s -X POST http://comms_gw:8081/fledge/scheduled/task \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PDS_POST",
    "type": "north",
    "plugin": "http_north",
    "schedule_type": 3,
    "schedule_repeat": 59,
    "schedule_enabled": true,
    "config": {
      "url": {
        "value": "http://api-historian:8000/productdatastream"
      }
    }
  }'

echo "HTTP North plugin PDS_POST has been configured."

sleep 2

curl -s -X POST http://comms_gw:8081/fledge/scheduled/task \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PQS_POST",
    "type": "north",
    "plugin": "http_north",
    "schedule_type": 3,
    "schedule_repeat": 59,
    "schedule_enabled": true,
    "config": {
      "url": {
        "value": "http://api-historian:8000/powerqualitydatastream"
      }
    }
  }'

echo "HTTP North plugin PQS_POST has been configured."

sleep 2

curl -s -X POST http://comms_gw:8081/fledge/scheduled/task \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ADS_POST",
    "type": "north",
    "plugin": "http_north",
    "schedule_type": 3,
    "schedule_repeat": 10,
    "schedule_enabled": true,
    "config": {
      "url": {
        "value": "http://api-historian:8000/analogdatastream"
      }
    }
  }'

echo "HTTP North plugin ADS_POST has been configured."

sleep 2

curl -s -X POST http://comms_gw:8081/fledge/scheduled/task \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DDS_POST",
    "type": "north",
    "plugin": "http_north",
    "schedule_type": 3,
    "schedule_repeat": 10,
    "schedule_enabled": true,
    "config": {
      "url": {
        "value": "http://api-historian:8000/digitaldatastream"
      }
    }
  }'

echo "HTTP North plugin DDS_POST has been configured."

sleep 2

echo "Create python35 North filters"

FILTER_NAME="calculate_ads_values"

# Check if the filter already exists
if curl -s http://comms_gw:8081/fledge/filter | grep -q "\"name\":\s*\"$FILTER_NAME\""; then
  echo "Filter '$FILTER_NAME' already exists. Skipping creation."
else
  echo "Filter '$FILTER_NAME' does not exist. Creating..."

  
curl --location 'http://comms_gw:8081/fledge/filter' \
--header 'Accept: application/json, text/plain, */*' \
--data '{"name":"calculate_ads_values","plugin":"python35","filter_config":{"enable":"true","config":{"_comment":"Channels can be VDC/ADC/Ambient,Oil level/OTI/OLTC/null","ANALOG_CHANNELS":[{"Channel":1,"ANASEN_CH1":"VDC"},{"Channel":2,"ANASEN_CH2":"ADC"},{"Channel":3,"ANASEN_CH3":"OLTC"},{"Channel":4,"ANASEN_CH4":"Ambient"},{"Channel":5,"ANASEN_CH5":null},{"Channel":6,"ANASEN_CH6":null}],"config":[{"VDC_MULT_FACTOR":0.0678},{"ADC_DIV_FACTOR":297.9},{"ADC_SUB_FACTOR":0},{"AMBIENT_MULT_FACTOR":195},{"AMBIENT_DIV_FACTOR":3000},{"OIL_LEVEL_MULT_FACTOR":50},{"OIL_LEVEL_DIV_FACTOR":1000},{"OTI_MULT_FACTOR":250},{"OTI_DIV_FACTOR":3000},{"WTI_MULT_FACTOR":1},{"WIL_DIV_FACTOR":1},{"OLTC_SUB_FACTOR":100},{"K1":0.9756},{"K2":2.0409545766299285e-8},{"K3":0.223577},{"K4":0},{"OLTC_TAP_CONFIG":[{"Tap":1,"Measured Value":100,"Expected Value":34650},{"Tap":2,"Measured Value":260,"Expected Value":34237},{"Tap":3,"Measured Value":406,"Expected Value":33825},{"Tap":4,"Measured Value":545,"Expected Value":33412},{"Tap":5,"Measured Value":686,"Expected Value":33000},{"Tap":6,"Measured Value":825,"Expected Value":32587},{"Tap":7,"Measured Value":990,"Expected Value":32175},{"Tap":8,"Measured Value":1145,"Expected Value":31762},{"Tap":9,"Measured Value":1248,"Expected Value":31350},{"Tap":10,"Measured Value":1389,"Expected Value":30937}]}]}}}'

curl --location --request PUT 'http://comms_gw:8081/fledge/filter/ADS_POST/pipeline?allow_duplicates=true&append_filter=true' \
--header 'Accept: application/json, text/plain, */*' \
--data '{"pipeline":["calculate_ads_values"],"files":[{"script":{}}]}'

curl --location 'http://comms_gw:8081/fledge/category/ADS_POST_calculate_ads_values/script/upload' \
--header 'Accept: application/json, text/plain, */*' \
--form 'script=@"/app/plugins/filter/ads/calculate_ads_values.py"'

echo "python35 North filters ADS has been configured."

fi

sleep 2

FILTER_NAME="generate_di_events"

# Check if the filter already exists
if curl -s http://comms_gw:8081/fledge/filter | grep -q "\"name\":\s*\"$FILTER_NAME\""; then
  echo "Filter '$FILTER_NAME' already exists. Skipping creation."
else
  echo "Filter '$FILTER_NAME' does not exist. Creating..."

 curl 'http:///comms_gw:8081/fledge/filter' \
--header 'Accept: application/json, text/plain, */*' \
--data '{"name":"generate_di_events","plugin":"python35","filter_config":{"enable":"true","config":{"_comment":"Channels can be CB/MasterTrip/OverCurrent/EarthFault/LRSwitch","DIGITAL_CHANNELS":[{"Channel":1,"Field":"Digi1"},{"Channel":2,"Field":"Digi2"},{"Channel":3,"Field":"Digi3"},{"Channel":4,"Field":"Digi4"},{"Channel":5,"Field":"Digi5"},{"Channel":6,"Field":"Digi6"},{"Channel":7,"Field":"Digi7"},{"Channel":8,"Field":"Digi8"}],"DIGITAL_CHANNEL_NAME":[{"Digi1":"CB"},{"Digi2":"CB"},{"Digi3":"OC"},{"Digi4":"EF"},{"Digi5":null},{"Digi6":null},{"Digi7":null},{"Digi8":null}],"DIGITAL_CHANNEL_TYPE":[{"Digi1":"DP1"},{"Digi2":"DP1"},{"Digi3":"SP1"},{"Digi4":"SP1"},{"Digi5":null},{"Digi6":null},{"Digi7":null},{"Digi8":null}],"DIGITAL_CHANNEL_STATE":[{"DP1":[{"0":"INVALID"},{"1":"OPEN"},{"2":"CLOSE"},{"3":"INTERMEDIATE"}]},{"SP1":[{"0":"OPEN"},{"1":"CLOSE"}]}]}}}'

curl --location --request PUT 'http://comms_gw:8081/fledge/filter/DDS_POST/pipeline?allow_duplicates=true&append_filter=true' \
--header 'Accept: application/json, text/plain, */*' \
--data '{"pipeline":["generate_di_events"],"files":[{"script":{}}]}'

curl --location 'http://comms_gw:8081/fledge/category/DDS_POST_generate_di_events/script/upload' \
--header 'Accept: application/json, text/plain, */*' \
--form 'script=@"/app/plugins/filter/dds/generate_di_events.py"'

echo "python35 North filters DDS has been configured."

fi

sleep 2

FILTER_NAME="generate_pds_limit_violations"

# Check if the filter already exists
if curl -s http://comms_gw:8081/fledge/filter | grep -q "\"name\":\s*\"$FILTER_NAME\""; then
  echo "Filter '$FILTER_NAME' already exists. Skipping creation."
else
  echo "Filter '$FILTER_NAME' does not exist. Creating..."

 curl --location 'http://comms_gw:8081/fledge/filter' \
--header 'Accept: application/json, text/plain, */*' \
--data '{"name":"generate_pds_limit_violations","plugin":"python35","filter_config":{"enable":"true","config":{"_comment":"Limit Violation PDS data","PARAMETERS":[{"Voltage_PN1":[{"LOWER_LIMIT":5940},{"UPPER_LIMIT":7260}]},{"Voltage_PN2":[{"LOWER_LIMIT":5940},{"UPPER_LIMIT":7260}]},{"Voltage_PN3":[{"LOWER_LIMIT":5940},{"UPPER_LIMIT":7260}]},{"Current1":[{"LOWER_LIMIT":-1},{"UPPER_LIMIT":120}]},{"Current2":[{"LOWER_LIMIT":0},{"UPPER_LIMIT":120}]},{"Current3":[{"LOWER_LIMIT":-1},{"UPPER_LIMIT":120}]},{"Frequency1":[{"LOWER_LIMIT":49.5},{"UPPER_LIMIT":50.5}]},{"Frequency2":[{"LOWER_LIMIT":49.5},{"UPPER_LIMIT":50.5}]},{"Frequency3":[{"LOWER_LIMIT":49.5},{"UPPER_LIMIT":50.5}]}]}}}'

curl --location --request PUT 'http://comms_gw:8081/fledge/filter/PDS_POST/pipeline?allow_duplicates=true&append_filter=true' \
--header 'Accept: application/json, text/plain, */*' \
--data '{"pipeline":["generate_pds_limit_violations"],"files":[{"script":{}}]}'

curl --location 'http://comms_gw:8081/fledge/category/PDS_POST_generate_pds_limit_violations/script/upload' \
--header 'Accept: application/json, text/plain, */*' \
--form 'script=@"/app/plugins/filter/pds/generate_pds_limit_violations.py"'

echo "python35 North filters PDS has been configured."

fi

sleep 2

FILTER_NAME="generate_pqs_limit_violations"

# Check if the filter already exists
if curl -s http://comms_gw:8081/fledge/filter | grep -q "\"name\":\s*\"$FILTER_NAME\""; then
  echo "Filter '$FILTER_NAME' already exists. Skipping creation."
else
  echo "Filter '$FILTER_NAME' does not exist. Creating..."

 curl --location 'http://comms_gw:8081/fledge/filter' \
 --header 'Accept: application/json, text/plain, */*' \
 --data '{"name":"generate_pqs_limit_violations","plugin":"python35","filter_config":{"enable":"true","config":{"_comment":"Limit Violation PQS data","PARAMETERS":[{"MinVtg_R":[{"LOWER_LIMIT":80},{"UPPER_LIMIT":120}]},{"MinVtg_Y":[{"LOWER_LIMIT":80},{"UPPER_LIMIT":120}]},{"MinVtg_B":[{"LOWER_LIMIT":80},{"UPPER_LIMIT":120}]},{"MaxVtg_R":[{"LOWER_LIMIT":100},{"UPPER_LIMIT":200}]},{"MaxVtg_Y":[{"LOWER_LIMIT":100},{"UPPER_LIMIT":200}]},{"MaxVtg_B":[{"LOWER_LIMIT":100},{"UPPER_LIMIT":200}]},{"AvgVtg_R":[{"LOWER_LIMIT":90},{"UPPER_LIMIT":110}]},{"AvgVtg_Y":[{"LOWER_LIMIT":90},{"UPPER_LIMIT":110}]},{"AvgVtg_B":[{"LOWER_LIMIT":90},{"UPPER_LIMIT":100}]}]}}}'

curl --location --request PUT 'http://comms_gw:8081/fledge/filter/PQS_POST/pipeline?allow_duplicates=true&append_filter=true' \
 --header 'Accept: application/json, text/plain, */*' \
 --data '{"pipeline":["generate_pqs_limit_violations"],"files":[{"script":{}}]}'

curl --location 'http://comms_gw:8081/fledge/category/PQS_POST_generate_pqs_limit_violations/script/upload' \
 --header 'Accept: application/json, text/plain, */*' \
 --form 'script=@"/app/plugins/filter/pqs/generate_pqs_limit_violations.py"'

echo "python35 North filters PQS has been configured."

fi

sleep 2

FILTER_NAME="stream_to_websocket"

if curl -s http://comms_gw:8081/fledge/filter | grep -q "\"name\":\s*\"$FILTER_NAME\""; then
  echo "Filter '$FILTER_NAME' already exists. Skipping creation."
else
  echo "Filter '$FILTER_NAME' does not exist. Creating..."

 curl --location 'http://comms_gw:8081/fledge/filter' \
 --header 'Accept: application/json, text/plain, */*' \
 --data '{"name":"stream_to_websocket","plugin":"python35","filter_config":{"enable":"true"}}'

curl --location --request PUT 'http://comms_gw:8081/fledge/filter/PDS_POST/pipeline?allow_duplicates=false&append_filter=true' \
 --header 'Accept: application/json, text/plain, */*' \
 --data '{"pipeline":["stream_to_websocket"],"files":[{"script":{}}]}'

curl --location 'http://comms_gw:8081/fledge/category/PDS_POST_stream_to_websocket/script/upload' \
 --header 'Accept: application/json, text/plain, */*' \
 --form 'script=@"/app/plugins/filter/ws/stream_to_websocket.py"'

echo "python35 North filters web socket streaming has been configured."

fi

sleep 2

# Start FastAPI app in background
echo "Starting FastAPI app..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload