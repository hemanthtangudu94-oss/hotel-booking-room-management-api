from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class RoomCreate(BaseModel):
    room_number: str = Field(min_length=1, max_length=10)
    room_type_id: int = Field(gt=0)
    floor: int = Field(gt=0)
    status: Literal["AVAILABLE", "MAINTENANCE", "CLEANING"] = "AVAILABLE"


class RoomResponse(BaseModel):
    id: int
    room_number: str
    room_type_id: int
    floor: int
    status: str

    model_config = ConfigDict(from_attributes=True)