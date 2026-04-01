from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Float, ForeignKey, DateTime
from datetime import datetime
from app.db.session import Base

class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)

    tyre_id: Mapped[int] = mapped_column(ForeignKey("tyres.id"))
    quantity: Mapped[int]
    purchase_price: Mapped[float]

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    