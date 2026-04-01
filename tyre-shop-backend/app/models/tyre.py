from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey
from app.db.session import Base

class Tyre(Base):
    __tablename__ = "tyres"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(50))
    size: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(50), nullable=True)

    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"))

    inventory = relationship("Inventory", back_populates="tyre")