from pydantic import BaseModel, Field
from typing import List, Optional


class SEEDSTEMDevicePayload(BaseModel):
    device_name: str = Field(..., example="MSEDCL-STMS1")
    enabled: bool = Field(..., example=True)
    comms_protocol: Optional[str] = Field(..., example="mqtt")
    mqtt_broker_host: Optional[str] = Field(None, example="mosquitto")
    mqtt_topic: Optional[str] = Field(None, example="STMS1/pdstop")
    asset_point_id: Optional[str] = Field(None, example="1")

class SEEDSTEMDeviceResponse(BaseModel):
    device_name: str
    enabled: bool
    comms_protocol: Optional[str]
    mqtt_broker_host: Optional[str]
    mqtt_topic: Optional[str]
    asset_point_id: Optional[str]

class SEEDSTEMDeviceResponses(BaseModel):
    devices: List[SEEDSTEMDevicePayload]


class DeviceSchedulePayload(BaseModel):
    device_name: str = Field(..., example="MSEDCL-STMS1")

