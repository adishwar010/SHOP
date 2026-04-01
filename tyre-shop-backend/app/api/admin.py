from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.user import User
from app.models.shop import Shop
from app.schemas.admin import CreateShopAdmin
from app.core.security import hash_password
from app.core.constants import Roles
from app.utils.shop_code import generate_shop_code

router = APIRouter()


@router.post("/create-shop-admin")
def create_shop_admin(data: CreateShopAdmin, db: Session = Depends(get_db)):

    # 🔹 Check if user exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # 🔹 Generate unique shop code
    shop_code = generate_shop_code()

    while db.query(Shop).filter(Shop.shop_code == shop_code).first():
        shop_code = generate_shop_code()

    # 🔹 Create shop
    shop = Shop(
        name=data.shop_name,
        gst_number=data.gst_number,
        shop_code=shop_code,
        owner_id=0  # temporary
    )

    db.add(shop)
    db.commit()
    db.refresh(shop)

    # 🔹 Create shop admin
    user = User(
        name=data.name,
        email=data.email,
        password=hash_password(data.password),
        role=Roles.SHOP_ADMIN,
        status="APPROVED",
        shop_id=shop.id
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # 🔹 Update shop owner
    shop.owner_id = user.id
    db.commit()

    return {
        "message": "Shop admin created successfully",
        "shop_code": shop_code
    }


