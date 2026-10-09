from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True,index=True)

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"),nullable=True)

    action: Mapped[str] = mapped_column(String(50),nullable=False)

    entity: Mapped[str] = mapped_column(String(50),nullable=False)

    entity_id: Mapped[int] = mapped_column(nullable=False)

    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc),nullable=False)
    