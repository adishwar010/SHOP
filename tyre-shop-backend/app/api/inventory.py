from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.tyre import Tyre
from app.models.inventory import Inventory
from app.models.purchase import Purchase
from app.models.sale import Sale
from app.models.user import User
from app.models.shop import Shop
from app.schemas.inventory import CreateTyre, PurchaseTyre, SellTyre
from app.utils.profits import get_average_purchase_price

from app.core.dependencies import get_current_user
from app.core.permissions import require_shop_admin, require_same_shop

router = APIRouter(tags=["Inventory"])


# 🔹 GET ALL TYRES
@router.get("/tyres")
def get_tyres(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.shop_id:
        raise HTTPException(status_code=403, detail="Not assigned to any shop")

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


# 🔹 CREATE TYRE (SHOP ADMIN ONLY)
@router.post("/tyre")
def create_tyre(
    data: CreateTyre,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_shop_admin(current_user)

    tyre = Tyre(
        brand=data.brand,
        size=data.size,
        type=data.type,
        shop_id=current_user.shop_id
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


# 🔹 PURCHASE (SHOP ADMIN ONLY)
@router.post("/purchase")
def purchase_tyre(
    data: PurchaseTyre,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_shop_admin(current_user)

    tyre = db.query(Tyre).filter(Tyre.id == data.tyre_id).first()

    if not tyre:
        raise HTTPException(status_code=404, detail="Tyre not found")

    # 🔐 SHOP ISOLATION
    require_same_shop(current_user, tyre.shop_id)

    inventory = db.query(Inventory).filter(Inventory.tyre_id == tyre.id).first()

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

#SELL TYRE
@router.post("/sell")
def sell_tyre(
    data: SellTyre,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.shop_id:
        raise HTTPException(status_code=403, detail="Not assigned to any shop")

    try:
        # 🔹 STEP 1: Get tyre (no lock needed here)
        tyre = db.query(Tyre).filter(Tyre.id == data.tyre_id).first()

        if not tyre:
            raise HTTPException(status_code=404, detail="Tyre not found")

        # 🔐 SHOP ISOLATION
        require_same_shop(current_user, tyre.shop_id)

        # 🔒 STEP 2: LOCK INVENTORY ROW (CRITICAL)
        inventory = (
            db.query(Inventory)
            .filter(Inventory.tyre_id == tyre.id)
            .with_for_update()
            .first()
        )

        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")

        # 🔥 STEP 3: CHECK STOCK AFTER LOCK
        if inventory.quantity < data.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")

        # 🔹 STEP 4: Get latest purchase price
        latest_purchase = (
            db.query(Purchase)
            .filter(Purchase.tyre_id == tyre.id)
            .order_by(Purchase.id.desc())
            .first()
        )

        if not latest_purchase:
            raise HTTPException(status_code=400, detail="No purchase history found")

        latest_cp = latest_purchase.purchase_price

        # 🔹 STEP 5: Get shop margin
        shop = db.query(Shop).filter(Shop.id == current_user.shop_id).first()

        margin = shop.margin_per_tyre if shop and shop.margin_per_tyre else 350

        calculated_price = latest_cp + margin

        # 🔹 STEP 6: Assistant override
        final_price = data.selling_price if data.selling_price else calculated_price

        # 🔹 STEP 7: No loss rule
        if final_price < latest_cp:
            raise HTTPException(status_code=400, detail="Cannot sell below cost price")

        # 🔥 STEP 8: UPDATE STOCK (SAFE NOW)
        inventory.quantity -= data.quantity

        # 🔹 STEP 9: CREATE SALE
        sale = Sale(
            tyre_id=tyre.id,
            quantity=data.quantity,
            selling_price=final_price,
            cost_price=latest_cp
        )

        db.add(sale)

        # 🔥 STEP 10: COMMIT (ENDS LOCK)
        db.commit()

        return {
            "message": "Sale recorded",
            "remaining_stock": inventory.quantity,
            "selling_price_used": final_price
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Sale failed")