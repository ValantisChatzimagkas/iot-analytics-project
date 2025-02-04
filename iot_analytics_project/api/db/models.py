from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class IoTData(BaseModel):
    timestamp: Optional[datetime] = Field(default=None, description="The timestamp when the data was recorded.")
    device_id: str = Field(..., description="The unique identifier for the IoT device.")
    voltage: float = Field(..., description="The voltage recorded by the device.")
    current: float = Field(..., description="The current recorded by the device.")
    device_type: str = Field(..., description="The type of IoT device.")
    location: str = Field(..., description="The location where the data was recorded.")

    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2025-01-01T12:34:56",
                "device_id": "4c118ca0-d470-4440-9a87-aff5f61bb138",
                "voltage": 3.7,
                "current": 0.5,
                "device_type": "Controller",
                "location": "warehouse"
            }
        }

