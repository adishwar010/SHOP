from sqlalchemy.orm import Session
from app.models.purchase import Purchase


def get_average_purchase_price(db: Session, tyre_id: int):
    purchases = db.query(Purchase).filter(Purchase.tyre_id == tyre_id).all()

    if not purchases:
        return 0

    total_cost = sum(p.purchase_price * p.quantity for p in purchases)
    total_qty = sum(p.quantity for p in purchases)

    return total_cost / total_qty if total_qty else 0