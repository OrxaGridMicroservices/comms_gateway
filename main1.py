from fastapi import FastAPI, HTTPException, Depends
import requests
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

load_dotenv()

app = FastAPI(
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    description="Fledge FastAPI and Swagger",
    version="0.1.0"
)

FLEDGE_BASE_URL = os.getenv("FLEDGE_BASE_URL", "http://fledge:8081")

class LoginPayload(BaseModel):
    username: str
    password: str

def get_auth_token():
    url = f"{FLEDGE_BASE_URL}/fledge/login"
    payload = {"username": "admin", "password": "fledge"}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get("token")
    else:
        raise Exception(f"Failed to authenticate: {response.text}")

@app.post("/comm_gw/login", tags=["Authentication Management"], summary="Return a token")
async def login(payload: LoginPayload):
    url = f"{FLEDGE_BASE_URL}/fledge/login"
    response = requests.post(url, json=payload.dict())
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

class ServicePayload(BaseModel):
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

@app.post("/comm_gw/service", tags=["Service Management"], summary="Create a Service")
async def create_service(payload: ServicePayload):
    """
    Create a new service in Fledge.

    The minimum required fields are 'name', 'type', and 'enabled'.  
    For north or south services, the 'plugin' field is required and you can also pass an optional 'config' for plugin configuration.
    """
    url = f"{FLEDGE_BASE_URL}/fledge/service"
    headers = {"Authorization": get_auth_token()}
    response = requests.post(url, json=payload.dict(exclude_unset=True), headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/service", tags=["Service Management"], summary="List all Services")
async def list_services():
    url = f"{FLEDGE_BASE_URL}/fledge/service"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.put("/comm_gw/service/{service_name}", tags=["Service Management"], summary="Update a Service")
async def update_service(service_name: str, payload: ServicePayload):
    # Delete the existing service
    delete_url = f"{FLEDGE_BASE_URL}/fledge/service/{service_name}"
    headers = {"Authorization": get_auth_token()}
    delete_response = requests.delete(delete_url, headers=headers)
    if delete_response.status_code != 200:
        raise HTTPException(status_code=delete_response.status_code, detail="Delete failed: " + delete_response.text)
    
    # Create a new service with updated configuration
    create_url = f"{FLEDGE_BASE_URL}/fledge/service"
    create_response = requests.post(create_url, json=payload.dict(exclude_unset=True), headers=headers)
    if create_response.status_code != 200:
        raise HTTPException(status_code=create_response.status_code, detail="Create failed: " + create_response.text)
    
    return create_response.json()


@app.delete("/comm_gw/service/{service_name}", tags=["Service Management"], summary="Delete a Service")
async def delete_service(service_name: str):
    url = f"{FLEDGE_BASE_URL}/fledge/service/{service_name}"
    headers = {"Authorization": get_auth_token()}
    response = requests.delete(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return {"message": "Service deleted successfully"}

# Endpoints for stopping and starting services via schedule

class SchedulePayload(BaseModel):
    schedule_name: str = Field(..., example="Sine")

@app.put("/comm_gw/schedule/disable", tags=["Service Management"], summary="Disable a Service")
async def disable_service(payload: SchedulePayload):
    """
    Disable the schedule associated with a service, effectively stopping it.
    """
    url = f"{FLEDGE_BASE_URL}/fledge/schedule/disable"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, json=payload.dict(), headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.put("/comm_gw/schedule/enable", tags=["Service Management"], summary="Enable a Service")
async def enable_service(payload: SchedulePayload):
    """
    Enable the schedule associated with a service, effectively starting it.
    """
    url = f"{FLEDGE_BASE_URL}/fledge/schedule/enable"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, json=payload.dict(), headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
