from fastapi import FastAPI, HTTPException, Query, Body
import requests
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import response_models

load_dotenv()

app = FastAPI(
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    description="comm_gw FastAPI and Swagger",
    version="0.1.0"
)

COMMS_GW_BASE_URL = os.getenv("COMMS_GW_BASE_URL")
FLEDGE_USERNAME = os.getenv("FLEDGE_USERNAME")
FLEDGE_PASSWORD = os.getenv("FLEDGE_PASSWORD")

class LoginPayload(BaseModel):
    username: str
    password: str

def get_auth_token():
    url = f"{COMMS_GW_BASE_URL}/fledge/login"
    payload = {"username": FLEDGE_USERNAME, "password": FLEDGE_PASSWORD}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get("token")
    else:
        raise Exception(f"Failed to authenticate: {response.text}")

@app.post("/comm_gw/login", tags=["Authentication Management"], summary="Return a token")
async def login(payload: LoginPayload):
    url = f"{COMMS_GW_BASE_URL}/fledge/login"
    response = requests.post(url, json=payload.dict())
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()



@app.get(
    "/comm_gw/seed-stem-device",
    tags=["Device Management"],
    summary="List SEED-STEM devices",
    response_model=response_models.SEEDSTEMDeviceResponses
)
async def list_seed_stem_devices(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page (max 100)")
):
    """
    Retrieve a paginated list of SEED-STEM devices registered in the Comms Gateway.
    """
    url = f"{COMMS_GW_BASE_URL}/fledge/service"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    services = response.json().get("services", [])

    # Filter only Southbound and Northbound services
    seed_stem_services = {
        service.get("name"): {
            "enabled": service.get("status") == "running",
            "comms_protocol": "mqtt-readings-binary"
        }
        for service in services
        if service.get("type", "").lower() in ["southbound", "northbound"]
    }

    # Apply pagination
    device_names = list(seed_stem_services.keys())
    start_index = (page - 1) * limit
    end_index = start_index + limit
    paginated_device_names = device_names[start_index:end_index]

    paginated_services = [
        response_models.SEEDSTEMDeviceListResponses(
            device_name=name,
            enabled=seed_stem_services[name]["enabled"],
            comms_protocol=seed_stem_services[name]["comms_protocol"]
        )
        for name in paginated_device_names
    ]

    return response_models.SEEDSTEMDeviceResponses(devices=paginated_services)


# featch all devices
async def get_all_seed_stem_devices():
    all_devices = []
    page = 1
    limit = 1000

    while True:
        response = await list_seed_stem_devices(page=page, limit=limit)
        if not response.devices:
            break
        all_devices.extend(response.devices)
        page += 1

    return all_devices


# https://fledge-iot.readthedocs.io/en/latest/rest_api_guide/03_RESTadmin.html#get-category
@app.get("/comm_gw/seed-stem-device/{device_name}",
         tags=["Device Management"],
         summary="Get SEED-STEM devices by device name",
         response_model=response_models.CreateSEEDSTEMDevicePayload)
async def get_category(device_name: str):
    # Retrieve all devices
    all_devices = await get_all_seed_stem_devices()
    devices_dict = {device.device_name: device.enabled for device in all_devices}

    # Check if the device exists
    if device_name not in devices_dict:
        raise HTTPException(status_code=404, detail="Device not found")

    enabled = devices_dict.get(device_name, False)

    url = f"{COMMS_GW_BASE_URL}/fledge/category/{device_name}"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    data = response.json()

    return {
        "device_name": device_name,
        "enabled": enabled,
        "comms_protocol": data.get("plugin", {}).get("value", ""),
        "mqtt_broker_host": data.get("brokerHost", {}).get("value", ""),
        "mqtt_topic": data.get("topic", {}).get("value", ""),
        "asset_point_id": data.get("assetName", {}).get("value", "")
    }

@app.post(
    "/comm_gw/seed-stem-device",
    tags=["Device Management"],
    summary="Create a SEED-STEM device",
    response_model=response_models.CreateSEEDSTEMDevicePayload
)
async def create_seed_stem_device(payload: response_models.CreateSEEDSTEMDevicePayload):
    """
    Create a new SEED-STEM device in Comms_gw.
    Required fields: 'device_name' and 'enabled'.
    For MQTT communication, 'comms_protocol' should be 'mqtt', with optional 'mqtt_broker_host', 'mqtt_topic', and 'asset_point_id'.
    """
    if payload.comms_protocol and payload.comms_protocol.lower() != "mqtt":
        raise HTTPException(status_code=400, detail={"message": "Invalid comms_protocol. Only 'mqtt' is supported."})

    url = f"{COMMS_GW_BASE_URL}/fledge/service"
    headers = {"Authorization": get_auth_token()}

    # Convert payload to dictionary, exclude None values
    payload_dict = payload.dict(exclude_none=True)
    
    # Rename 'device_name' to 'name'
    payload_dict["name"] = payload_dict.pop("device_name")
    payload_dict["type"] = "south"
    # Validate protocol and set plugin
    if payload.comms_protocol == "mqtt":
        payload_dict["plugin"] = "mqtt-readings-binary"
    else:
        raise HTTPException(status_code=400, detail="Invalid comms_protocol. Only 'mqtt' is supported.")

    # Build config dictionary
    payload_dict["config"] = {}

    if payload.mqtt_broker_host:
        payload_dict["config"]["brokerHost"] = {"value": payload.mqtt_broker_host}
    if payload.mqtt_topic:
        payload_dict["config"]["topic"] = {"value": payload.mqtt_topic}
    if payload.asset_point_id is not None:
        payload_dict["config"]["assetName"] = {"value": str(payload.asset_point_id)}

    # Send request to Comms GW
    try:
        response = requests.post(url, json=payload_dict, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        response_data = response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail={"message": str(e)})
    except ValueError:
        raise HTTPException(status_code=response.status_code, detail={"message": response.text})

    # Return the structured response
    return response_models.CreateSEEDSTEMDevicePayload(**payload.dict(exclude_none=True))

@app.put("/comm_gw/seed-stem-device/{device_name}",
         tags=["Device Management"],
         summary="Update SEED-STEM device by device name",
         response_model=response_models.CreateSEEDSTEMDevicePayload)
async def update_seed_stem_device(
    device_name: str,
    update_payload: response_models.CreateSEEDSTEMDevicePayload
):

    headers = {"Authorization": get_auth_token()}

    # Fields to update in Fledge
    update_fields = {
        "brokerHost": update_payload.mqtt_broker_host,
        "topic": update_payload.mqtt_topic,
        "assetName": update_payload.asset_point_id
    }

    for key, value in update_fields.items():
        url = f"{COMMS_GW_BASE_URL}/fledge/category/{device_name}/{key}"
        response = requests.put(url, json={"value": str(value)}, headers=headers)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to update '{key}': {response.text}"
            )

    # check device status after update
    refreshed_devices = await get_all_seed_stem_devices()
    enabled = next((d.enabled for d in refreshed_devices if d.device_name == device_name), False)

    # Fetch plugin (comms_protocol) info
    plugin_url = f"{COMMS_GW_BASE_URL}/fledge/category/{device_name}/plugin"
    plugin_response = requests.get(plugin_url, headers=headers)
    if plugin_response.status_code != 200:
        raise HTTPException(
            status_code=plugin_response.status_code,
            detail=f"Failed to fetch comms_protocol: {plugin_response.text}"
        )
    comms_protocol = plugin_response.json().get("value", "")

    return {
        "device_name": device_name,
        "enabled": enabled,
        "comms_protocol": comms_protocol,
        "mqtt_broker_host": update_payload.mqtt_broker_host,
        "mqtt_topic": update_payload.mqtt_topic,
        "asset_point_id": update_payload.asset_point_id
    }

@app.delete(
    "/comm_gw/seed-stem-device/{device_name}",
    response_model=response_models.DeleteSEEDSTEMDeviceResponse, 
    tags=["Device Management"],
    summary="Delete a SEED-STEM device"
)
async def delete_seed_stem_device(device_name: str):
    url = f"{COMMS_GW_BASE_URL}/fledge/service/{device_name}"
    headers = {"Authorization": get_auth_token()}

    response = requests.delete(url, headers=headers)

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Device not found")

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Delete failed: " + response.text)
    
    return {
      "result": f"SEED-STEM device with name {device_name} deleted successfully!",
      "statusCode": 200
   }


@app.put(
    "/comm_gw/seed_stem_device/disable",
    tags=["Device Management"],
    summary="Disable a SEED-STEM device",
    response_model=response_models.DeviceScheduleResponseModel
    
)
async def disable_seed_stem_device(payload: response_models.DeviceSchedulePayload):
    url = f"{COMMS_GW_BASE_URL}/fledge/schedule/disable"
    headers = {"Authorization": get_auth_token()}
    
    payload_dict = payload.dict(exclude_unset=True)
    payload_dict["schedule_name"] = payload_dict.pop("device_name")

    response = requests.put(url, json=payload_dict, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response_models.DeviceScheduleResponseModel(
        device_name=payload.device_name,  
        enabled=False
    )

@app.put(
    "/comm_gw/seed_stem_device/enable",
    tags=["Device Management"],
    summary="Enable a SEED-STEM device",
    response_model=response_models.DeviceScheduleResponseModel
)
async def enable_seed_stem_device(payload: response_models.DeviceSchedulePayload):
    url = f"{COMMS_GW_BASE_URL}/fledge/schedule/enable"
    headers = {"Authorization": get_auth_token()}
    
    payload_dict = payload.dict(exclude_unset=True)
    payload_dict["schedule_name"] = payload_dict.pop("device_name")

    response = requests.put(url, json=payload_dict, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response_models.DeviceScheduleResponseModel(
        device_name=payload.device_name,  
        enabled=True
    )
