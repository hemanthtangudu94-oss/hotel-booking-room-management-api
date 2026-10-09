from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class BookingCreate(BaseModel):
    room_id: int = Field(gt=0)
    check_in: date
    check_out: date


class BookingResponse(BaseModel):
    id: int
    user_id: int
    room_id: int
    check_in: date
    check_out: date
    status: str
    total_amount: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)