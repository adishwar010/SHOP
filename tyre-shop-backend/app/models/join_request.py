from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, ForeignKey, String, DateTime
from datetime import datetime, timedelta
from app.db.session import Base

class JoinRequest(Base):
    __tablename__ = "join_requests"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"))

    status: Mapped[str] = mapped_column(String(20), default="PENDING")

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.utcnow() + timedelta(days=7)
    )