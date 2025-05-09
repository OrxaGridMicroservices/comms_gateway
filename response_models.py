from pydantic import BaseModel, Field
from typing import List, Optional

class SEEDSTEMDeviceListResponses(BaseModel):
    device_name: str = Field(..., example="MSEDCL-STMS1")
    enabled: bool = Field(..., example=True)
    comms_protocol: Optional[str] = Field(..., example="mqtt")

class SEEDSTEMDeviceResponses(BaseModel):
    devices: List[SEEDSTEMDeviceListResponses]

class CreateSEEDSTEMDevicePayload(BaseModel):
    device_name: str = Field(..., example="MSEDCL-STMS1")
    enabled: bool = Field(..., example=True)
    comms_protocol: Optional[str] = Field(..., example="mqtt")
    mqtt_broker_host: Optional[str] = Field(None, example="mosquitto")
    mqtt_topic: Optional[str] = Field(None, example="STMS1/pdstop")
    mqtt_username: Optional[str] = Field(None, example="mqtt_user")     # New
    mqtt_password: Optional[str] = Field(None, example="mqtt_pass")
    asset_point_id: Optional[str] = Field(None, example="1")


class DeleteSEEDSTEMDeviceResponse(BaseModel):
    result: str = Field(
        ...,
        example=["SEED-STEM device deleted successfully"],
        description="Response message"
    )
    statusCode: int = Field(..., example=[200])

class DeviceSchedulePayload(BaseModel):
    device_name: str = Field(..., example="MSEDCL-STMS1")

class DeviceScheduleResponseModel(BaseModel):
    device_name: str = Field(..., example="MSEDCL-STMS1")
    enabled: bool = Field(..., example=True)

