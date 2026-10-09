from sqlalchemy import Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class RoomType(Base):
    __tablename__ = "room_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name:Mapped[str] = mapped_column(String(50), unique=True,nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    price_per_night: Mapped[float] = mapped_column(Numeric(10, 2),nullable=False)
    