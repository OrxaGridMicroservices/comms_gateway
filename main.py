from fastapi import FastAPI, HTTPException, Query, Path, Body
import requests
import os
from dotenv import load_dotenv
from pydantic import BaseModel,Field
import response_models

load_dotenv()

app = FastAPI(
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    description="Fladge FastAPI and Swagger",
    version="0.1.0")

FLEDGE_BASE_URL = os.getenv("COMMS_GW_BASE_URL", "http://comms_gw:8081")

COMMS_GW_BASE_URL = os.getenv("COMMS_GW_BASE_URL")
FLEDGE_USERNAME = os.getenv("FLEDGE_USERNAME")
FLEDGE_PASSWORD = os.getenv("FLEDGE_PASSWORD")


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

@app.post("/comm_gw/login", tags=["Authentication Management"],summary="return a token")
async def login(payload: LoginPayload):
    url = f"{FLEDGE_BASE_URL}/fledge/login"
    response = requests.post(url, json=payload.dict())

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json()

@app.put("/comm_gw/logout", tags=["Authentication Management"],summary="Terminate the current login session")
async def logout():
    url = f"{FLEDGE_BASE_URL}/fledge/logout"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url,headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
@app.put("/comm_gw/{user_id}/logout",tags=["Authentication Management"],summary="Terminate the login session for user’s all active sessions")
async def logout_user(userid: int):
    url = f"{FLEDGE_BASE_URL}/fledge/{userid}/logout"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url,headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

class NewUserPayload(BaseModel):
    username: str = "david"
    password: str = "Inv1nc!ble"
    role_id: int = 1
    description: str = None
    real_name: str = "David Brent"
    access_method: str = "any"

@app.post("/comm_gw/admin/user", tags=["User Management"],summary="add a new user to Fledge’s user database")
async def add_user(payload: NewUserPayload):
    url = f"{FLEDGE_BASE_URL}/fledge/admin/user"
    headers = {"Authorization": get_auth_token()}
    response = requests.post(url, json=payload.dict(),headers=headers)

    if response.status_code == 400:
        raise HTTPException(status_code=400, detail="Bad Request - Invalid Input")
    elif response.status_code == 403:
        raise HTTPException(status_code=403, detail="Forbidden - Access Denied")
    elif response.status_code == 409:
        raise HTTPException(status_code=409, detail="Conflict - Resource Already Exists")
    elif response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json()

@app.get("/comm_gw/user", tags=["User Management"],summary="Retrieve data on all users")
async def get_users():
    url = f"{FLEDGE_BASE_URL}/fledge/user"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url,headers=headers)
    if response.status_code == 400:
        raise HTTPException(status_code=400, detail="Bad Request - Invalid Input")
    elif response.status_code == 403:
        raise HTTPException(status_code=403, detail="Forbidden - Access Denied")
    elif response.status_code == 409:
        raise HTTPException(status_code=409, detail="Conflict - Resource Already Exists")
    elif response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

class UpdateUserPayload(BaseModel):
    real_name: str = "david"

@app.put("/comm_gw/user", tags=["User Management"],summary="Allows a user to update their own user information")
async def update_user(payload: UpdateUserPayload):
    url = f"{FLEDGE_BASE_URL}/fledge/user"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, json=payload.dict(),headers=headers)
    if response.status_code == 400:
        raise HTTPException(status_code=400, detail="Bad Request - Invalid Input")
    elif response.status_code == 403:
        raise HTTPException(status_code=403, detail="Forbidden - Access Denied")
    elif response.status_code == 409:
        raise HTTPException(status_code=409, detail="Conflict - Resource Already Exists")
    elif response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

class UpdatePasswordPayload(BaseModel):
    current_password: str
    new_password: str

@app.put("/comm_gw/user/{userid}/password", tags=["User Management"],summary="change the password for the current user")
async def update_password(userid: int, payload: UpdatePasswordPayload):
    url = f"{FLEDGE_BASE_URL}/fledge/user/{userid}/password"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, json=payload.dict(),headers=headers)
    if response.status_code == 400:
        raise HTTPException(status_code=400, detail="Bad Request - Invalid Input")
    elif response.status_code == 403:
        raise HTTPException(status_code=403, detail="Forbidden - Access Denied")
    elif response.status_code == 409:
        raise HTTPException(status_code=409, detail="Conflict - Resource Already Exists")
    elif response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

class UpdateAdminUserPayload(BaseModel):
    description: str="david"
    access_method: str="cert/any/cert"
    real_name: str="David Brent"

@app.put("/comm_gw/admin/user", tags=["User Management"],summary="An admin user can update any user’s information")
async def admin_update_user(payload: UpdateAdminUserPayload):
    url = f"{FLEDGE_BASE_URL}/fledge/admin/user"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, json=payload.dict(),headers=headers)

    if response.status_code == 400:
        raise HTTPException(status_code=400, detail="Incomplete or badly formed request payload")
    elif response.status_code == 403:
        raise HTTPException(status_code=403, detail="A user without admin permissions tried to add a new user")
    elif response.status_code == 409:
        raise HTTPException(status_code=409, detail="The username is already in use")
    elif response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json()

@app.delete("/comm_gw/admin/user/{userID}/delete", tags=["User Management"],summary="delete a user")
async def delete_user(userID: int):
    url = f"{FLEDGE_BASE_URL}/fledge/admin/user/{userID}/delete"
    headers = {"Authorization": get_auth_token()}
    response = requests.delete(url,headers=headers)
    if response.status_code == 400:
        raise HTTPException(status_code=400, detail="Bad Request - Invalid Input")
    elif response.status_code == 403:
        raise HTTPException(status_code=403, detail="Forbidden - Access Denied")
    elif response.status_code == 409:
        raise HTTPException(status_code=409, detail="Conflict - Resource Already Exists")
    elif response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
    return response.json()

@app.get("/comm_gw/audit", tags=["Audit Management"],summary="list of audit trail entries sorted with most recent first")
async def get_audit(   
    skip: int = Query(default=None, description="Number of records to skip"),
    limit: int = Query(default=None, description="Maximum number of records to return"),
    source: str = Query(default=None, description="Source of the audit records"),
    severity: str = Query(default=None, description="Severity level of the audit records")
    ):
    url = f"{FLEDGE_BASE_URL}/fledge/audit"
    params = {
        "skip": skip,
        "limit": limit,
        "source": source,
        "severity": severity
    }
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json()

class CreateAuditPayload(BaseModel):
    source: str="LOGGN"
    severity: str="FAILURE"
    details: object={'message':'Internal System Error' }

@app.post("/comm_gw/audit", tags=["Audit Management"], summary="create a new audit trail entry.")
async def create_audit(payload: CreateAuditPayload):
    headers = {"Authorization": get_auth_token()}
    response = requests.post(f"{FLEDGE_BASE_URL}/fledge/audit", json=payload.dict(), headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

##Configuration Management¶
# Category Management

@app.get("/comm_gw/category", tags=["Category Management"],summary="list of known categories in the configuration database")
async def get_categories():
    headers = {"Authorization": get_auth_token()}
    response = requests.get(f"{FLEDGE_BASE_URL}/fledge/category",headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/category/{name}",tags=["Category Management"],summary="onfiguration items in the given category")
async def get_category(name: str):
    url = f"{FLEDGE_BASE_URL}/fledge/category/{name}"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url,headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/category/{name}/{item}",tags=["Category Management"],summary="configuration item in the given category")
async def get_category_item(name: str = "rest_api", item: str = "httpsPort"):
    url = f"{FLEDGE_BASE_URL}/fledge/category/{name}/{item}"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.put("/comm_gw/category/{name}/{item}",tags=["Category Management"],summary="set the configuration item value in the given category")
async def update_category_item(name: str, item: str, payload: dict={"value":"1996"}):
    url = f"{FLEDGE_BASE_URL}/fledge/category/{name}/{item}"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, json=payload,headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.delete("/comm_gw/category/{name}/{item}/value",tags=["Category Management"],summary="unset the value of the configuration item in the given category")
async def delete_category_item(name: str, item: str):
    url = f"{FLEDGE_BASE_URL}/fledge/category/{name}/{item}/value"
    headers = {"Authorization": get_auth_token()}
    response = requests.delete(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

# Define Config Item model with default values
class ConfigItem(BaseModel):
    description: str
    type: str = "string"
    default: str

# Define Category Payload model with default payload
class CategoryPayload(BaseModel):
    key: str = "My Configuration"
    description: str = "This is my new configuration"
    value: dict[str, ConfigItem] = {
        "item one": ConfigItem(description="The first item", type = "string",default="one"),
        "item two": ConfigItem(description="The second item", type = "string",default="two"),
        "item three": ConfigItem(description="The third item", type = "string",default="three")
    }

@app.post("/comm_gw/category", tags=["Category Management"], summary="Create a new category")
async def create_category(payload: CategoryPayload = CategoryPayload()):
    url = f"{FLEDGE_BASE_URL}/fledge/category"
    headers = {"Authorization": get_auth_token()}
    response = requests.post(url, json=payload.dict(),headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

# Task Management
@app.get("/comm_gw/task", tags=["Task Management"], summary="list of all known task running or completed" )
async def get_tasks( 
    name: str = Query(default=None, description="an optional task name to filter on, only executions of the particular task will be reported."),
    state: str = Query(default=None, description="an optional query parameter that will return only those tasks in the given state")):
    params = {
        "name": name,
        "state": state,
    }
    headers = {"Authorization": get_auth_token()}
    response = requests.get(f"{FLEDGE_BASE_URL}/fledge/task", params=params, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/task/latest", tags=["Task Management"],summary="list of most recent task execution for each name")
async def get_latest_task(
    name: str = Query(default=None, description="an optional task name to filter on, only executions of the particular task will be reported."),
    state: str = Query(default=None, description="an optional query parameter that will return only those tasks in the given state")):
    params = {
        "name": name,
        "state": state,
    }
    headers = {"Authorization": get_auth_token()}
    response = requests.get(f"{FLEDGE_BASE_URL}/task/latest", params=params, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/task/{id}", tags=["Task Management"],summary=" task information for the given task")
async def get_task(id: str):
    url = f"{FLEDGE_BASE_URL}/fledge/task/{id}"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.put("/comm_gw/task/{id}/cancel", tags=["Task Management"], summary="cancel a task")
async def cancel_task(id: str):
    url = f"{FLEDGE_BASE_URL}/fledge/task/{id}/cancel"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

#Other Administrative API calls
# Endpoint to shut down Fledge
@app.put("/comm_gw/shutdown", tags=["Fledge Management"], summary="Shut down Fledge")
async def shutdown_fledge():
    url = f"{FLEDGE_BASE_URL}/fledge/shutdown"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

# Endpoint to restart Fledge
@app.put("/comm_gw/restart", tags=["Fledge Management"], summary="Restart Fledge")
async def restart_fledge():
    url = f"{FLEDGE_BASE_URL}/fledge/restart"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/ping", tags=["Fledge Management"],summary="liveness of Fledge")
async def ping():
    url = f"{FLEDGE_BASE_URL}/fledge/ping"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json()

#Statistics
@app.get("/comm_gw/statistics", tags=["Statistics"], summary="Get Fledge Statistics")
async def get_statistics():
    url = f"{FLEDGE_BASE_URL}/fledge/statistics"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()



@app.get("/comm_gw/statistics/history", tags=["Statistics"], summary="Get Fledge Statistics History")
async def get_statistics_history(limit: int = Query(default=10, description="Number of records to fetch")):
    url = f"{FLEDGE_BASE_URL}/fledge/statistics/history?limit={limit}"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.get("/comm_gw/statistics/rate", tags=["Statistics"], summary="Get Fledge Statistics Rate")
async def get_statistics_rate(
    statistics: str = Query(..., description="Name of the statistic to fetch"),
    periods: int = Query(..., description="Number of periods for the statistics")
):
    url = f"{FLEDGE_BASE_URL}/fledge/statistics/rate?statistics={statistics}&periods={periods}"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

#Asset Tacker
@app.get("/comm_gw/track", tags=["Asset Tracker"], summary="Get Asset Tracking Records")
async def get_asset_track(
    asset: str = Query(None, description="Asset name to filter by"),
    event: str = Query(None, description="Event type to filter by"),
    service: str = Query(None, description="Service name to filter by")
):
    url = f"{FLEDGE_BASE_URL}/fledge/track"
    params = {
        "asset": asset,
        "event": event,
        "service": service
    }
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.put(
    "/comm_gw/track/service/{service_name}/asset/{asset_name}/event/{event_name}",
    tags=["Asset Tracker"], 
    summary="Track a Specific Asset Event"
)
async def track_specific_asset_event(
    service_name: str = Path(..., description="Service name"),
    asset_name: str = Path(..., description="Asset name"),
    event_name: str = Path(..., description="Event name")
):
    url = f"{FLEDGE_BASE_URL}/fledge/track/service/{service_name}/asset/{asset_name}/event/{event_name}"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return {"message": "Asset tracking updated successfully"}

#Repository Configuration
@app.post("/comm_gw/repository", tags=["Repository Configuration"], summary="Add Repository Configuration")
async def add_repository(
    payload: dict = Body(
        ...,
        example={
            "url": "http://archives.fledge-iot.org",
            "version": "latest"
        }
    )
):
    url = f"{FLEDGE_BASE_URL}/fledge/repository"
    headers = {"Authorization": get_auth_token()}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return {"message": "Repository configuration added successfully"}


@app.put("/comm_gw/update", tags=["Repository Configuration"], summary="Update Packages")
async def update_packages():
    url = f"{FLEDGE_BASE_URL}/fledge/update"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return {"message": "Packages updated successfully"}


#Service Status
@app.get("/comm_gw/service", tags=["Service Status"], summary="List All Services")
async def list_services():
    url = f"{FLEDGE_BASE_URL}/fledge/service"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/service/filter", tags=["Service Status"], summary="Filter Services by Type")
async def filter_services(service_type: str = Query(..., example="Southbound")):
    url = f"{FLEDGE_BASE_URL}/fledge/service?type={service_type}"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

#South and North Services
@app.get("/comm_gw/south", tags=["South and North Services"], summary="List South Services")
async def list_south_services():
    url = f"{FLEDGE_BASE_URL}/fledge/south"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/south", tags=["South and North Services"], summary="List North Services")
async def list_south_services():
    url = f"{FLEDGE_BASE_URL}/fledge/north"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

#Service Types
@app.get("/comm_gw/service/installed", tags=["Service Types"], summary="List Installed Services")
async def list_installed_services():
    url = f"{FLEDGE_BASE_URL}/fledge/service/installed"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/service/available", tags=["Service Types"], summary="List Available Services")
async def list_available_services():
    url = f"{FLEDGE_BASE_URL}/fledge/service/available"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.post("/comm_gw/service/install", tags=["Service Types"], summary="Install a Service")
async def install_service(format: str = "repository", name: str = "fledge-service-notification"):
    url = f"{FLEDGE_BASE_URL}/fledge/service?action=install"
    payload = {
        "format": format,
        "name": name
    }
    headers = {"Authorization": get_auth_token()}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

#Creating A Service
class BrokerHostConfig(BaseModel):
    value: str = Field(..., example="mosquitto")

class TopicConfig(BaseModel):
    value: str = Field(..., example="STMS2/pdstop")

class AssetNameConfig(BaseModel):
    value: str = Field(..., example="STMS1_pds_Feeder")

class Config(BaseModel):
    brokerHost: BrokerHostConfig
    topic: TopicConfig
    assetName: AssetNameConfig

class ServicePayload(BaseModel):
    name: str = Field(..., example="MSEDCL-STMS2")
    type: str = Field(..., example="south")
    plugin: str = Field(..., example="mqtt-readings-binary")
    config: Config
    enabled: bool = Field(..., example=True)
    
@app.post("/comm_gw/service", tags=["Creating A Service"], summary="Create a Service")
async def create_service(
    payload: ServicePayload
):
    url = f"{FLEDGE_BASE_URL}/fledge/service"
    headers = {"Authorization": get_auth_token()}
    response = requests.post(url, json=payload.dict(),headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

#Stopping and Starting Services¶
@app.put("/comm_gw/schedule/disable", tags=["Stopping and Starting Services"], summary="Stop a Service")
async def stop_service(payload: dict = Body({"schedule_name": "Sine"})):
    url = f"{FLEDGE_BASE_URL}/fledge/schedule/disable"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.put("/comm_gw/schedule/enable", tags=["Stopping and Starting Services"], summary="Start a Service")
async def start_service(payload: dict = Body({"schedule_name": "Sine"})):
    url = f"{FLEDGE_BASE_URL}/fledge/schedule/enable"
    headers = {"Authorization": get_auth_token()}
    response = requests.put(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

#Deleting a Service
@app.delete("/comm_gw/service/{service_name}", tags=["Deleting a Service"], summary="Delete a Service")
async def delete_service(service_name: str):
    url = f"{FLEDGE_BASE_URL}/fledge/service/{service_name}"
    headers = {"Authorization": get_auth_token()}
    response = requests.delete(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

#Browsing Assets
@app.get("/comm_gw/asset", tags=["Browsing Assets"], summary="List all assets")
async def get_assets():
    url = f"{FLEDGE_BASE_URL}/fledge/asset"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url,headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/asset/{code}", tags=["Browsing Assets"], summary="Retrieve asset by code")
async def get_asset_by_code(
    code: str,
    limit: int = Query(10, le=100),  # Default limit 10, max 100
    skip: int = Query(0),
    seconds: int = Query(None),
    minutes: int = Query(None),
    hours: int = Query(None),
    previous: bool = Query(False)
):
    url = f"{FLEDGE_BASE_URL}/fledge/asset/{code}?limit={limit}&skip={skip}"
    if seconds is not None:
        url += f"&seconds={seconds}"
    if minutes is not None:
        url += f"&minutes={minutes}"
    if hours is not None:
        url += f"&hours={hours}"
    if previous:
        url += "&previous=true"
        
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/asset/{code}/{reading}", tags=["Browsing Assets"], summary="Retrieve asset reading")
async def get_asset_reading(
    code: str,
    reading: str,
    limit: int = Query(10, le=100),
    skip: int = Query(0),
    seconds: int = Query(None),
    minutes: int = Query(None),
    hours: int = Query(None),
    previous: bool = Query(False)
):
    url = f"{FLEDGE_BASE_URL}/fledge/asset/{code}/{reading}?limit={limit}&skip={skip}"
    if seconds is not None:
        url += f"&seconds={seconds}"
    if minutes is not None:
        url += f"&minutes={minutes}"
    if hours is not None:
        url += f"&hours={hours}"
    if previous:
        url += "&previous=true"
    
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/asset/{code}/{reading}/summary", tags=["Browsing Assets"], summary="Retrieve asset reading summary")
async def get_asset_reading_summary(code: str, reading: str):
    url = f"{FLEDGE_BASE_URL}/fledge/asset/{code}/{reading}/summary"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/asset/timespan", tags=["Browsing Assets"], summary="Retrieve asset timespan")
async def get_asset_timespan():
    url = f"{FLEDGE_BASE_URL}/fledge/asset/timespan"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/asset/{code}/timespan", tags=["Browsing Assets"], summary="Retrieve asset timespan by code")
async def get_asset_timespan_by_code(code: str):
    url = f"{FLEDGE_BASE_URL}/fledge/asset/{code}/timespan"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/asset/{code}/{reading}/series", tags=["Browsing Assets"], summary="Retrieve asset reading series")
async def get_asset_reading_series(
    code: str,
    reading: str,
    limit: int = Query(10, le=100),
    skip: int = Query(0),
    seconds: int = Query(None),
    minutes: int = Query(None),
    hours: int = Query(None),
    previous: bool = Query(False)
):
    url = f"{FLEDGE_BASE_URL}/fledge/asset/{code}/{reading}/series?limit={limit}&skip={skip}"
    if seconds is not None:
        url += f"&seconds={seconds}"
    if minutes is not None:
        url += f"&minutes={minutes}"
    if hours is not None:
        url += f"&hours={hours}"
    if previous:
        url += "&previous=true"
    
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

#Purge Readings
@app.delete("/comm_gw/asset", tags=["Purge Readings"], summary="Purge all asset readings")
async def purge_all_assets():
    url = f"{FLEDGE_BASE_URL}/fledge/asset"
    headers = {"Authorization": get_auth_token()}
    response = requests.delete(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return {"message": "All asset readings purged successfully."}

@app.delete("/comm_gw/asset/{asset_name}", tags=["Purge Readings"], summary="Purge asset readings by name")
async def purge_asset_by_name(asset_name: str):
    url = f"{FLEDGE_BASE_URL}/fledge/asset/{asset_name}"
    headers = {"Authorization": get_auth_token()}
    response = requests.delete(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return {"message": f"Asset readings for {asset_name} purged successfully."}

# Persisted Data
@app.get("/comm_gw/service/{service_name}/persist", tags=["Persisted Data"], summary="Get persisted plugins for a service")
async def get_persisted_plugins(service_name: str):
    url = f"{FLEDGE_BASE_URL}/fledge/service/{service_name}/persist"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/comm_gw/service/{service_name}/plugin/{plugin_name}/data", tags=["Persisted Data"], summary="Get persisted data for the plugin")
async def get_plugin_data(service_name: str, plugin_name: str):
    url = f"{FLEDGE_BASE_URL}/fledge/service/{service_name}/plugin/{plugin_name}/data"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.post("/comm_gw/service/{service_name}/plugin/{plugin_name}/data", tags=["Persisted Data"], summary="Post data to the plugin")
async def post_plugin_data(service_name: str, plugin_name: str, data: dict):
    url = f"{FLEDGE_BASE_URL}/fledge/service/{service_name}/plugin/{plugin_name}/data"
    headers = {"Authorization": get_auth_token()}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return {"message": "Data posted to plugin successfully."}

@app.delete("/comm_gw/service/{service_name}/plugin/{plugin_name}/data", tags=["Persisted Data"], summary="Delete persisted data for the plugin")
async def delete_plugin_data(service_name: str, plugin_name: str):
    url = f"{FLEDGE_BASE_URL}/fledge/service/{service_name}/plugin/{plugin_name}/data"
    headers = {"Authorization": get_auth_token()}
    response = requests.delete(url,headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return {"message": f"Persisted data for plugin {plugin_name} deleted successfully."}


#Grafana Display
@app.get("/comm_gw/ping", tags=["Grafana"], summary="Ping the Fledge server")
async def ping_fledge():
    url = f"{FLEDGE_BASE_URL}/fledge/ping"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return {"message": "Ping successful", "status_code": response.status_code}


@app.get("/comm_gw/asset/{asset_code}", tags=["Grafana"], summary="Retrieve asset data")
async def get_asset_data(asset_code: str, limit: int = 2):
    url = f"{FLEDGE_BASE_URL}/fledge/asset/{asset_code}?limit={limit}"
    headers = {"Authorization": get_auth_token()}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


# User defined API

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