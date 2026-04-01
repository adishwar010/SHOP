from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.tyre import Tyre
from app.models.inventory import Inventory
from app.models.purchase import Purchase
from app.models.sale import Sale
from app.models.user import User
from app.schemas.inventory import CreateTyre, PurchaseTyre, SellTyre

router = APIRouter()


# GET ALL TYRES
@router.get("/tyres")
def get_tyres(db: Session = Depends(get_db), user_id: int = 1):

    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.shop_id:
        raise HTTPException(status_code=403, detail="Not authorized")

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

# 🔹 CREATE TYRE
@router.post("/tyre")
def create_tyre(data: CreateTyre, db: Session = Depends(get_db), user_id: int = 1):
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.shop_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    tyre = Tyre(
        brand=data.brand,
        size=data.size,
        type=data.type,
        shop_id=user.shop_id
    )

    db.add(tyre)
    db.commit()
    db.refresh(tyre)

    # 🔥 create inventory entry
    inventory = Inventory(
        tyre_id=tyre.id,
        quantity=0
    )

    db.add(inventory)
    db.commit()

    return {"message": "Tyre created", "tyre_id": tyre.id}


# 🔹 PURCHASE (ADD STOCK)
@router.post("/purchase")
def purchase_tyre(data: PurchaseTyre, db: Session = Depends(get_db), user_id: int = 1):
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.shop_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    tyre = db.query(Tyre).filter(Tyre.id == data.tyre_id).first()

    if not tyre:
        raise HTTPException(status_code=404, detail="Tyre not found")

    inventory = db.query(Inventory).filter(Inventory.tyre_id == tyre.id).first()

    # 🔥 TRANSACTION START
    try:
        inventory.quantity += data.quantity

        purchase = Purchase(
            tyre_id=tyre.id,
            quantity=data.quantity,
            purchase_price=data.purchase_price
        )

        db.add(purchase)
        db.commit()

    except:
        db.rollback()
        raise HTTPException(status_code=500, detail="Purchase failed")

    return {"message": "Stock updated", "new_quantity": inventory.quantity}


# 🔹 SELL (REDUCE STOCK)
@router.post("/sell")
def sell_tyre(data: SellTyre, db: Session = Depends(get_db), user_id: int = 1):
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.shop_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    tyre = db.query(Tyre).filter(Tyre.id == data.tyre_id).first()

    if not tyre:
        raise HTTPException(status_code=404, detail="Tyre not found")

    inventory = db.query(Inventory).filter(Inventory.tyre_id == tyre.id).first()

    if inventory.quantity < data.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    # 🔥 TRANSACTION (CRITICAL)
    try:
        inventory.quantity -= data.quantity

        sale = Sale(
            tyre_id=tyre.id,
            quantity=data.quantity,
            selling_price=data.selling_price
        )

        db.add(sale)
        db.commit()

    except:
        db.rollback()
        raise HTTPException(status_code=500, detail="Sale failed")

    return {"message": "Sale recorded", "remaining_stock": inventory.quantity}