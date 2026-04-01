from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.deps import get_db
from app.models.user import User
from app.models.tyre import Tyre
from app.models.sale import Sale
from app.models.inventory import Inventory

from app.core.dependencies import get_current_user
from app.core.permissions import require_shop_admin

router = APIRouter(tags=["Dashboard"])


# 💰 TOTAL PROFIT (FIXED)
@router.get("/profit")
def get_profit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_shop_admin(current_user)

    tyres = db.query(Tyre).filter(Tyre.shop_id == current_user.shop_id).all()

    total_profit = 0

    for tyre in tyres:
        sales = db.query(Sale).filter(Sale.tyre_id == tyre.id).all()

        for sale in sales:
            # 🔥 CORRECT LOGIC
            profit = (sale.selling_price - sale.cost_price) * sale.quantity
            total_profit += profit

    return {"total_profit": round(total_profit, 2)}


# 📊 STOCK OVERVIEW (UNCHANGED)
@router.get("/stock")
def stock_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_shop_admin(current_user)

    tyres = db.query(Tyre).filter(Tyre.shop_id == current_user.shop_id).all()

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


# 🔥 TOP SELLING TYRES (UNCHANGED)
@router.get("/top-selling")
def top_selling(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_shop_admin(current_user)

    result = db.query(
        Sale.tyre_id,
        func.sum(Sale.quantity).label("total_sold")
    ).join(Tyre, Tyre.id == Sale.tyre_id)\
     .filter(Tyre.shop_id == current_user.shop_id)\
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


# ⚠️ LOW STOCK ALERT (UNCHANGED)
@router.get("/low-stock")
def low_stock(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_shop_admin(current_user)

    threshold = 5

    result = db.query(
        Tyre.id,
        Tyre.brand,
        Tyre.size,
        Inventory.quantity
    ).join(Inventory, Inventory.tyre_id == Tyre.id)\
     .filter(
         Tyre.shop_id == current_user.shop_id,
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


# 📈 SALES SUMMARY (UNCHANGED)
@router.get("/sales-summary")
def sales_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_shop_admin(current_user)

    total_items = db.query(func.sum(Sale.quantity))\
        .join(Tyre, Tyre.id == Sale.tyre_id)\
        .filter(Tyre.shop_id == current_user.shop_id)\
        .scalar() or 0

    total_revenue = db.query(func.sum(Sale.quantity * Sale.selling_price))\
        .join(Tyre, Tyre.id == Sale.tyre_id)\
        .filter(Tyre.shop_id == current_user.shop_id)\
        .scalar() or 0

    return {
        "total_items_sold": int(total_items),
        "total_revenue": float(total_revenue)
    }