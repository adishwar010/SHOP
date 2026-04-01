from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.deps import get_db
from app.models.user import User
from app.models.tyre import Tyre
from app.models.sale import Sale
from app.models.purchase import Purchase
from app.models.inventory import Inventory
from app.utils.profits import get_average_purchase_price

router = APIRouter()


# 🔹 HELPER: VALIDATE USER
def get_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.shop_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return user


# 💰 TOTAL PROFIT
@router.get("/profit")
def get_profit(db: Session = Depends(get_db), user_id: int = 1):

    user = get_user(db, user_id)

    tyres = db.query(Tyre).filter(Tyre.shop_id == user.shop_id).all()

    total_profit = 0

    for tyre in tyres:
        avg_price = get_average_purchase_price(db, tyre.id)

        sales = db.query(Sale).filter(Sale.tyre_id == tyre.id).all()

        for sale in sales:
            profit = (sale.selling_price - avg_price) * sale.quantity
            total_profit += profit

    return {"total_profit": round(total_profit, 2)}


# 📊 STOCK OVERVIEW
@router.get("/stock")
def stock_overview(db: Session = Depends(get_db), user_id: int = 1):

    user = get_user(db, user_id)

    tyres = db.query(Tyre).filter(Tyre.shop_id == user.shop_id).all()

    result = []

    for tyre in tyres:
        inventory = db.query(Inventory).filter(
            Inventory.tyre_id == tyre.id
        ).first()

        result.append({
            "tyre_id": tyre.id,
            "brand": tyre.brand,
            "size": tyre.size,
            "type": tyre.type,
            "stock": inventory.quantity if inventory else 0
        })

    return result


# 🔥 TOP SELLING TYRES
@router.get("/top-selling")
def top_selling(db: Session = Depends(get_db), user_id: int = 1):

    user = get_user(db, user_id)

    result = db.query(
        Sale.tyre_id,
        func.sum(Sale.quantity).label("total_sold")
    ).join(Tyre, Tyre.id == Sale.tyre_id)\
     .filter(Tyre.shop_id == user.shop_id)\
     .group_by(Sale.tyre_id)\
     .order_by(func.sum(Sale.quantity).desc())\
     .all()

    return [
        {
            "tyre_id": r.tyre_id,
            "total_sold": int(r.total_sold)
        }
        for r in result
    ]


# ⚠️ LOW STOCK ALERT
@router.get("/low-stock")
def low_stock(db: Session = Depends(get_db), user_id: int = 1):

    user = get_user(db, user_id)

    threshold = 5

    result = db.query(
        Tyre.id,
        Tyre.brand,
        Tyre.size,
        Inventory.quantity
    ).join(Inventory, Inventory.tyre_id == Tyre.id)\
     .filter(
         Tyre.shop_id == user.shop_id,
         Inventory.quantity < threshold
     ).all()

    return [
        {
            "tyre_id": r.id,
            "brand": r.brand,
            "size": r.size,
            "stock": r.quantity
        }
        for r in result
    ]


# 📈 SALES SUMMARY
@router.get("/sales-summary")
def sales_summary(db: Session = Depends(get_db), user_id: int = 1):

    user = get_user(db, user_id)

    total_items = db.query(func.sum(Sale.quantity))\
        .join(Tyre, Tyre.id == Sale.tyre_id)\
        .filter(Tyre.shop_id == user.shop_id)\
        .scalar() or 0

    total_revenue = db.query(func.sum(Sale.quantity * Sale.selling_price))\
        .join(Tyre, Tyre.id == Sale.tyre_id)\
        .filter(Tyre.shop_id == user.shop_id)\
        .scalar() or 0

    return {
        "total_items_sold": int(total_items),
        "total_revenue": float(total_revenue)
    }