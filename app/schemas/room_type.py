from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

class RoomTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    capacity: int = Field(gt=0)
    price_per_night: Decimal = Field(gt=0)


class RoomTypeUpdate(RoomTypeCreate):
    pass


class RoomTypePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    capacity: int | None = Field(default=None, gt=0)
    price_per_night: Decimal | None = Field(default=None, gt=0)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def require_changes(self):
        changes = self.model_dump(exclude_unset=True)
        if not changes or any(value is None for key, value in changes.items() if key != "description"):
            raise ValueError("Provide at least one valid field to update")
        return self


class RoomTypeResponse(BaseModel):
    id: int
    name: str
    description: str | None
    capacity: int
    price_per_night: Decimal

    model_config = ConfigDict(from_attributes=True)
