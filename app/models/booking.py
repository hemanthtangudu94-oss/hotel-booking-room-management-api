from datetime import date, datetime, timezone

from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"),nullable=False)

    check_in: Mapped[date] = mapped_column(Date, nullable=False)

    check_out: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="CONFIRMED", nullable=False)

    total_amount: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
