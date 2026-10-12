from decimal import Decimal

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BookingCreate(BaseModel):
    room_id: int = Field(gt=0)
    check_in: date
    check_out: date


class BookingUpdate(BookingCreate):
    pass


class BookingPatch(BaseModel):
    room_id: int | None = Field(default=None, gt=0)
    check_in: date | None = None
    check_out: date | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def require_non_null_changes(self):
        changes = self.model_dump(exclude_unset=True)
        if not changes or any(value is None for value in changes.values()):
            raise ValueError("Provide at least one non-null field to update")
        return self


class BookingResponse(BaseModel):
    id: int
    user_id: int
    room_id: int
    check_in: date
    check_out: date
    status: str
    total_amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
