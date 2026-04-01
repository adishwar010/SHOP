from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime
from datetime import datetime
from app.db.session import Base

class Shop(Base):
    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    gst_number: Mapped[str] = mapped_column(String(50))

    shop_code: Mapped[str] = mapped_column(String(20), unique=True)  # 🔥 REQUIRED

    owner_id: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    users = relationship("User", back_populates="shop")