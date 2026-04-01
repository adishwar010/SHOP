from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, DateTime
from datetime import datetime, date
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password: Mapped[str] = mapped_column(String(200))

    role: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="PENDING")

    shop_id: Mapped[int | None] = mapped_column(
        ForeignKey("shops.id"), nullable=True
    )

    dob: Mapped[date | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    shop = relationship("Shop", back_populates="users")