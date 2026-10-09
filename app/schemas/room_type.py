from pydantic import BaseModel, ConfigDict, Field

class RoomTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    capacity: int = Field(gt=0)
    price_per_night: float = Field(gt=0)

class RoomTypeResponse(BaseModel):
    id: int
    name: str
    description: str | None
    capacity: int
    price_per_night: float

    model_config = ConfigDict(from_attributes=True)
