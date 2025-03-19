from fastapi import FastAPI, HTTPException
import requests
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

load_dotenv()

app = FastAPI(
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    description="comm_gw FastAPI and Swagger",
    version="0.1.0"
)

COMMS_GW_BASE_URL = os.getenv("COMMS_GW_BASE_URL", "http://fledge:8081")

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

class SEEDSTEMDevicePayload(BaseModel):
    name: str = Field(..., example="MSEDCL-STMS1")
    type: str = Field(..., example="south")
    enabled: bool = Field(..., example=True)
    plugin: Optional[str] = Field(None, example="mqtt-readings-binary")  # required for north/south services
    config: Optional[Dict[str, Any]] = Field(
        None,
        example={
            "brokerHost": {"value": "mosquitto"},
            "topic": {"value": "STMS2/pdstop"},
            "assetName": {"value": "STMS1_pds_Feeder"}
        }
    )

@app.post("/comm_gw/seed-stem-device", tags=["Device Management"], summary="Create a SEED-STEM device")
async def create_seed_stem_device(payload: SEEDSTEMDevicePayload):
    """
    Create a new service in Comms_gw.
    The minimum required fields are 'name', 'type', and 'enabled'.
    For north or south services, the 'plugin' field is required, and you can also pass an optional 'config'.
    """
    url = f"{COMMS_GW_BASE_URL}/fledge/service"
    headers = {"Authorization": get_auth_token()}
    response = requests.post(url, json=payload.dict(exclude_unset=True), headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/seed-stem-device", tags=["Device Management"], summary="List all SEED-STEM devices")
async def list_seed_stem_devices():
    url = f"{COMMS_GW_BASE_URL}/fledge/service"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.put("/comm_gw/seed-stem-device/{device_name}", tags=["Device Management"], summary="Update a SEED-STEM device")
async def update_seed_stem_device(device_name: str, payload: SEEDSTEMDevicePayload):
    delete_url = f"{COMMS_GW_BASE_URL}/fledge/service/{device_name}"
    headers = {"Authorization": get_auth_token()}
    delete_response = requests.delete(delete_url, headers=headers)
    if delete_response.status_code != 200:
        raise HTTPException(status_code=delete_response.status_code, detail="Delete failed: " + delete_response.text)
    
    create_url = f"{COMMS_GW_BASE_URL}/fledge/service"
    create_response = requests.post(create_url, json=payload.dict(exclude_unset=True), headers=headers)
    if create_response.status_code != 200:
        raise HTTPException(status_code=create_response.status_code, detail="Create failed: " + create_response.text)
    
    return create_response.json()

@app.delete("/comm_gw/seed-stem-device/{device_name}", tags=["Device Management"], summary="Delete a SEED-STEM device")
async def delete_seed_stem_device(device_name: str):
    url = f"{COMMS_GW_BASE_URL}/fledge/service/{device_name}"
    headers = {"Authorization": get_auth_token()}
    response = requests.delete(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return {"message": "SEED-STEM device deleted successfully"}

class SchedulePayload(BaseModel):
    service_name: str = Field(..., example="MSEDCL-STMS1")

@app.put("/comm_gw/seed_stem_device/disable", tags=["Device Management"], summary="Disable a SEED-STEM device")
async def disable_seed_stem_device(payload: SchedulePayload):
    url = f"{COMMS_GW_BASE_URL}/fledge/schedule/disable"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, json=payload.dict(), headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.put("/comm_gw/seed_stem_device/enable", tags=["Device Management"], summary="Enable a SEED-STEM device")
async def enable_seed_stem_device(payload: SchedulePayload):
    url = f"{COMMS_GW_BASE_URL}/fledge/schedule/enable"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, json=payload.dict(), headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
