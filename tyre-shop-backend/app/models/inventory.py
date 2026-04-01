from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey
from app.db.session import Base

class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True)

    tyre_id: Mapped[int] = mapped_column(ForeignKey("tyres.id"))
    quantity: Mapped[int] = mapped_column(default=0)

    tyre = relationship("Tyre", back_populates="inventory")