from pydantic import BaseModel, Field
from typing import List, Optional

class SEEDSTEMDeviceInfo(BaseModel):
    name: str = Field(..., example="MSEDCL-STMS1")
    type: str = Field(..., example="Southbound")
    address: str = Field(..., example="localhost")
    management_port: int = Field(..., example=39163)
    service_port: int = Field(..., example=42327)
    protocol: str = Field(..., example="http")
    status: str = Field(..., example="running")

class SEEDSTEMDeviceListResponse(BaseModel):
    services: List[SEEDSTEMDeviceInfo]

class SEEDSTEMDevicePayload(BaseModel):
    device_name: str = Field(..., example="MSEDCL-STMS1")
    enabled: bool = Field(..., example=True)
    comms_protocol: Optional[str] = Field(..., example="mqtt")
    mqtt_broker_host: Optional[str] = Field(None, example="mosquitto")
    mqtt_topic: Optional[str] = Field(None, example="STMS2/pdstop")
    asset_point_id: Optional[int] = Field(None, example=1)

class SEEDSTEMDeviceResponse(BaseModel):
    name: str = Field(..., example="MSEDCL-STMS1")
    id: str = Field(..., example="e99318bf-0024-4803-b28c-702cd6db728c")


class DeleteSEEDSTEMDeviceResponse(BaseModel):
    result: str = Field(
        ...,
        examples=["SEED-STEM device deleted successfully"],
        description="Response message"
    )
    statusCode: int = Field(..., examples=[200])

class SchedulePayload(BaseModel):
    device_name: str = Field(..., example="MSEDCL-STMS1")

class ScheduleResponseModel(BaseModel):
    scheduleId: str = Field(..., example="9f9d4539-676f-4d67-b5ba-425b6df334a8")
    status: bool = Field(..., example=True)
    message: str = Field(..., example="Schedule successfully disabled")
