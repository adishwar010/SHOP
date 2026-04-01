from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.db.deps import get_db
from app.models.user import User
from app.models.tyre import Tyre
from app.models.sale import Sale
from app.models.inventory import Inventory

from app.core.dependencies import get_current_user
from app.core.permissions import require_shop_admin

router = APIRouter(tags=["Dashboard"])


# 🔥 NEW: UNIFIED DASHBOARD API (PRODUCTION)
@router.get("/")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_shop_admin(current_user)

    shop_id = current_user.shop_id

    # -------------------------
    # 💰 TOTAL REVENUE & PROFIT (OPTIMIZED)
    # -------------------------
    revenue_profit = db.query(
        func.coalesce(func.sum(Sale.selling_price * Sale.quantity), 0),
        func.coalesce(func.sum((Sale.selling_price - Sale.cost_price) * Sale.quantity), 0)
    ).join(Tyre, Tyre.id == Sale.tyre_id)\
     .filter(Tyre.shop_id == shop_id)\
     .first()

    total_revenue = float(revenue_profit[0] or 0)
    total_profit = float(revenue_profit[1] or 0)

    # -------------------------
    # 📦 TOTAL STOCK
    # -------------------------
    total_stock = db.query(
        func.coalesce(func.sum(Inventory.quantity), 0)
    ).join(Tyre, Tyre.id == Inventory.tyre_id)\
     .filter(Tyre.shop_id == shop_id)\
     .scalar()

    # -------------------------
    # ⚠️ LOW STOCK ALERT
    # -------------------------
    low_stock = db.query(
        Tyre.id,
        Tyre.brand,
        Tyre.size,
        Inventory.quantity
    ).join(Inventory, Inventory.tyre_id == Tyre.id)\
     .filter(Tyre.shop_id == shop_id, Inventory.quantity < 5)\
     .all()

    # -------------------------
    # 📅 SALES TODAY
    # -------------------------
    today = datetime.utcnow().date()

    sales_today = db.query(
        func.coalesce(func.sum(Sale.selling_price * Sale.quantity), 0)
    ).join(Tyre, Tyre.id == Sale.tyre_id)\
     .filter(
        Tyre.shop_id == shop_id,
        func.date(Sale.created_at) == today
    ).scalar()

    # -------------------------
    # 📅 SALES THIS WEEK
    # -------------------------
    week_start = today - timedelta(days=7)

    sales_week = db.query(
        func.coalesce(func.sum(Sale.selling_price * Sale.quantity), 0)
    ).join(Tyre, Tyre.id == Sale.tyre_id)\
     .filter(
        Tyre.shop_id == shop_id,
        Sale.created_at >= week_start
    ).scalar()

    # -------------------------
    # 🧾 RECENT SALES
    # -------------------------
    recent_sales = db.query(
        Sale.id,
        Tyre.brand,
        Tyre.size,
        Sale.quantity,
        Sale.selling_price,
        Sale.created_at
    ).join(Tyre, Tyre.id == Sale.tyre_id)\
     .filter(Tyre.shop_id == shop_id)\
     .order_by(Sale.id.desc())\
     .limit(5)\
     .all()

    return {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "total_stock": int(total_stock or 0),

        "low_stock": [
            {
                "tyre_id": t.id,
                "brand": t.brand,
                "size": t.size,
                "stock": t.quantity
            }
            for t in low_stock
        ],

        "sales_today": float(sales_today or 0),
        "sales_this_week": float(sales_week or 0),

        "recent_sales": [
            {
                "sale_id": s.id,
                "brand": s.brand,
                "size": s.size,
                "quantity": s.quantity,
                "price": s.selling_price,
                "date": s.created_at
            }
            for s in recent_sales
        ]
    }


# 🔥 FIXED: PROFIT (REMOVED N+1)
@router.get("/profit")
def get_profit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_shop_admin(current_user)

    total_profit = db.query(
        func.coalesce(func.sum((Sale.selling_price - Sale.cost_price) * Sale.quantity), 0)
    ).join(Tyre, Tyre.id == Sale.tyre_id)\
     .filter(Tyre.shop_id == current_user.shop_id)\
     .scalar()

    return {"total_profit": float(total_profit or 0)}


# 🔥 FIXED: STOCK OVERVIEW (NO LOOP)
@router.get("/stock")
def stock_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_shop_admin(current_user)

    result = db.query(
        Tyre.id,
        Tyre.brand,
        Tyre.size,
        Tyre.type,
        Inventory.quantity
    ).join(Inventory, Inventory.tyre_id == Tyre.id)\
     .filter(Tyre.shop_id == current_user.shop_id)\
     .all()

    return [
        {
            "tyre_id": r.id,
            "brand": r.brand,
            "size": r.size,
            "type": r.type,
            "stock": r.quantity or 0
        }
        for r in result
    ]


# 🔥 UNCHANGED (ALREADY OPTIMIZED)
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


# 🔥 UNCHANGED (ALREADY GOOD)
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


# 🔥 FIXED: SALES SUMMARY (SAFE DEFAULTS)
@router.get("/sales-summary")
def sales_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_shop_admin(current_user)

    total_items = db.query(
        func.coalesce(func.sum(Sale.quantity), 0)
    ).join(Tyre, Tyre.id == Sale.tyre_id)\
     .filter(Tyre.shop_id == current_user.shop_id)\
     .scalar()

    total_revenue = db.query(
        func.coalesce(func.sum(Sale.quantity * Sale.selling_price), 0)
    ).join(Tyre, Tyre.id == Sale.tyre_id)\
     .filter(Tyre.shop_id == current_user.shop_id)\
     .scalar()

    return {
        "total_items_sold": int(total_items or 0),
        "total_revenue": float(total_revenue or 0)
    }