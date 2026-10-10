from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    booking_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0)
    payment_method: str = Field(min_length=2, max_length=20)


class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    amount: Decimal
    status: str
    payment_method: str
    paid_at: datetime | None

    model_config = ConfigDict(from_attributes=True)