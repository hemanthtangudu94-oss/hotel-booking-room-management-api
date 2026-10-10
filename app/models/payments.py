from datetime import datetime

from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Index

from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"),nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(10,2),nullable=False)

    status: Mapped[str] = mapped_column(String(20),default="PENDING", nullable=False)

    payment_method: Mapped[str] = mapped_column(String(20),nullable=False)

    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index(
            "uq_paid_payment_per_booking",
            "booking_id",
            unique=True,
            sqlite_where=(status == "PAID")
        ),
    )
