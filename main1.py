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
    response_model=response_models.SEEDSTEMDeviceListResponse
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
        response_models.SEEDSTEMDeviceInfo(**service)
        for service in services
        if service.get("type", "").lower() in ["southbound", "northbound"]
    ]

    # Apply pagination
    start_index = (page - 1) * limit
    end_index = start_index + limit
    paginated_services = seed_stem_services[start_index:end_index]

    return {"services": paginated_services}

@app.post(
    "/comm_gw/seed-stem-device",
    tags=["Device Management"],
    summary="Create a SEED-STEM device",
    response_model=response_models.SEEDSTEMDeviceResponse
)
async def create_seed_stem_device(payload: response_models.SEEDSTEMDevicePayload):
    """
    Create a new service in Comms_gw.
    The minimum required fields are 'device_name' and 'enabled'.
    For north or south services, the 'comms_protocol' field is required, and you can also pass an optional 'mqtt_broker_host', 'mqtt_topic', and 'asset_point_id'.
    """
    url = f"{COMMS_GW_BASE_URL}/fledge/service"
    headers = {"Authorization": get_auth_token()}
    payload_dict = payload.dict(exclude_unset=True)

    # Rename 'device_name' to 'name'
    payload_dict["name"] = payload_dict.pop("device_name")

    # Set 'type' to 'south' (since it's no longer passed in the request)
    payload_dict["type"] = "south"

    # Validate comms_protocol and set plugin
    if payload.comms_protocol == "mqtt":
        payload_dict["plugin"] = "mqtt-readings-binary"
    else:
        raise HTTPException(status_code=400, detail={"message": "Invalid comms_protocol. Only 'mqtt' is supported."})

    payload_dict["config"] = {}

    if payload.mqtt_broker_host:
        payload_dict["config"]["brokerHost"] = {"value": payload.mqtt_broker_host}
    if payload.mqtt_topic:
        payload_dict["config"]["topic"] = {"value": payload.mqtt_topic}
    if payload.asset_point_id is not None:
        payload_dict["config"]["assetName"] = {"value": str(payload.asset_point_id)}

    # Send request to Comms GW
    response = requests.post(url, json=payload_dict, headers=headers)

    if response.status_code != 200:
        error_message = response.json().get("message", response.text)
        raise HTTPException(status_code=response.status_code, detail={"message": error_message})

    return response.json()


@app.put(
    "/comm_gw/seed-stem-device/{device_name}",
    tags=["Device Management"],
    summary="Update a SEED-STEM device",
    response_model=response_models.SEEDSTEMDeviceResponse
)
async def update_seed_stem_device(device_name: str, payload: response_models.SEEDSTEMDevicePayload):
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

    return create_response.json()

@app.delete(
    "/comm_gw/seed-stem-device/{device_name}",
    tags=["Device Management"],
    summary="Delete a SEED-STEM device",
    response_model=response_models.DeleteSEEDSTEMDeviceResponse
)
async def delete_seed_stem_device(device_name: str):
    url = f"{COMMS_GW_BASE_URL}/fledge/service/{device_name}"
    headers = {"Authorization": get_auth_token()}
    
    response = requests.delete(url, headers=headers)

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Device not found")

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Delete failed: " + response.text)
    return {"result": "SEED-STEM device deleted successfully", "statusCode": 200}


@app.put(
    "/comm_gw/seed_stem_device/disable",
    tags=["Device Management"],
    summary="Disable a SEED-STEM device",
    response_model=response_models.ScheduleResponseModel
    
)
async def disable_seed_stem_device(payload: response_models.SchedulePayload):
    url = f"{COMMS_GW_BASE_URL}/fledge/schedule/disable"
    headers = {"Authorization": get_auth_token()}
    
    payload_dict = payload.dict(exclude_unset=True)
    payload_dict["schedule_name"] = payload_dict.pop("device_name")

    response = requests.put(url, json=payload_dict, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json()

@app.put(
    "/comm_gw/seed_stem_device/enable",
    tags=["Device Management"],
    summary="Enable a SEED-STEM device",
    response_model=response_models.ScheduleResponseModel
)
async def enable_seed_stem_device(payload: response_models.SchedulePayload):
    url = f"{COMMS_GW_BASE_URL}/fledge/schedule/enable"
    headers = {"Authorization": get_auth_token()}
    
    payload_dict = payload.dict(exclude_unset=True)
    payload_dict["schedule_name"] = payload_dict.pop("device_name")

    response = requests.put(url, json=payload_dict, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json()
