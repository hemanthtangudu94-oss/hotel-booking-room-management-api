from typing import Literal
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class RoomCreate(BaseModel):
    room_number: str = Field(min_length=1, max_length=10)
    room_type_id: int = Field(gt=0)
    floor: int = Field(gt=0)
    status: Literal["AVAILABLE", "MAINTENANCE", "CLEANING"] = "AVAILABLE"


class RoomUpdate(BaseModel):
    room_number: str = Field(min_length=1, max_length=10)
    room_type_id: int = Field(gt=0)
    floor: int = Field(gt=0)
    status: Literal["AVAILABLE", "MAINTENANCE", "CLEANING"]


class RoomPatch(BaseModel):
    room_number: str | None = Field(default=None, min_length=1, max_length=10)
    room_type_id: int | None = Field(default=None, gt=0)
    floor: int | None = Field(default=None, gt=0)
    status: Literal["AVAILABLE", "MAINTENANCE", "CLEANING"] | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def require_non_null_changes(self):
        changes = self.model_dump(exclude_unset=True)
        if not changes or any(value is None for value in changes.values()):
            raise ValueError("Provide at least one non-null field to update")
        return self


class RoomResponse(BaseModel):
    id: int
    room_number: str
    room_type_id: int
    floor: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class AvailableRoomResponse(BaseModel):
    id: int
    room_number: str
    floor: int
    status: Literal["AVAILABLE"]
    room_type_name: str
    capacity: int
    price_per_night: Decimal
