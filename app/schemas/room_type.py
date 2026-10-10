from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

class RoomTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    capacity: int = Field(gt=0)
    price_per_night: Decimal = Field(gt=0)

class RoomTypeResponse(BaseModel):
    id: int
    name: str
    description: str | None
    capacity: int
    price_per_night: Decimal

    model_config = ConfigDict(from_attributes=True)
