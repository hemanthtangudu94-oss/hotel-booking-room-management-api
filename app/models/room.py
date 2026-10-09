from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    room_number: Mapped[str] = mapped_column(String(10),unique=True,nullable=False)

    room_type_id: Mapped[int] = mapped_column(ForeignKey("room_types.id"),nullable=False)

    floor: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="AVAILABLE",nullable=False)
