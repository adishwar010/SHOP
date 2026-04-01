from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Float, ForeignKey, DateTime
from datetime import datetime
from app.db.session import Base


class Sale(Base):
    __tablename__ = "sales"

    # 🔑 Primary Key
    id: Mapped[int] = mapped_column(primary_key=True)

    # 🔗 Foreign Key
    tyre_id: Mapped[int] = mapped_column(ForeignKey("tyres.id"), nullable=False)

    # 🔢 Quantity sold
    quantity: Mapped[int] = mapped_column(nullable=False)

    # 💰 Selling price per unit
    selling_price: Mapped[float] = mapped_column(nullable=False)

    # 🔥 NEW: Cost price per unit at time of sale
    cost_price: Mapped[float] = mapped_column(nullable=False)

    # 🕒 Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )