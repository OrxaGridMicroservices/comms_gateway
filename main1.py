from fastapi import FastAPI, HTTPException, Query
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

COMMS_GW_BASE_URL = os.getenv("COMMS_GW_BASE_URL", "http://comms_gw:8081")

class LoginPayload(BaseModel):
    username: str
    password: str

def get_auth_token():
    url = f"{COMMS_GW_BASE_URL}/fledge/login"
    payload = {"username": "admin", "password": "fledge"}
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
    "/api/seed-stem-device",
    tags=["Device Management"],
    summary="List SEED-STEM devices with pagination",
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
    seed_stem_services = [
        response_models.SEEDSTEMDeviceListResponses(
            device_name=service.get("name"),
            enabled=(service.get("status") == "running"),
            comms_protocol="mqtt-readings-binary"
        )
        for service in services
        if service.get("type", "").lower() in ["southbound", "northbound"]
    ]

    total_devices = len(seed_stem_services)  # Total count before slicing

    # Apply pagination
    start_index = (page - 1) * limit
    end_index = start_index + limit
    paginated_services = seed_stem_services[start_index:end_index]

    return response_models.SEEDSTEMDeviceResponses(devices=paginated_services)


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
    payload_dict["plugin"] = "mqtt-readings-binary"
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

@app.put(
    "/comm_gw/seed-stem-device/{device_name}",
    tags=["Device Management"],
    summary="Update a SEED-STEM device",
    response_model=response_models.CreateSEEDSTEMDevicePayload
)
async def update_seed_stem_device(device_name: str, payload: response_models.CreateSEEDSTEMDevicePayload):
    """
    Update an existing SEED-STEM device by deleting and recreating it with new values.
    """
    delete_url = f"{COMMS_GW_BASE_URL}/fledge/service/{device_name}"
    headers = {"Authorization": get_auth_token()}
    
    # Delete the existing device
    delete_response = requests.delete(delete_url, headers=headers)
    if delete_response.status_code != 200:
        raise HTTPException(status_code=delete_response.status_code, detail="Delete failed: " + delete_response.text)

    # Prepare the payload for re-creation
    payload_dict = payload.dict(exclude_unset=True)
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

    # Create the updated device
    create_url = f"{COMMS_GW_BASE_URL}/fledge/service"
    create_response = requests.post(create_url, json=payload_dict, headers=headers)
    if create_response.status_code != 200:
        raise HTTPException(status_code=create_response.status_code, detail="Create failed: " + create_response.text)

    return response_models.CreateSEEDSTEMDevicePayload(**payload.dict(exclude_none=True))

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
