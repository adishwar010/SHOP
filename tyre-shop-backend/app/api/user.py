from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.user import User

from app.core.dependencies import get_current_user
from app.core.constants import Roles

router = APIRouter(tags=["User"])

@router.get("/debug-auth")
def debug_auth(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }


# 🔹 GET ALL USERS (ADMIN ONLY)
@router.get("/all")
def get_all_users(db: Session = Depends(get_db), user_id: int = 1):

    user = db.query(User).filter(User.id == user_id).first()

    if not user or user.role != Roles.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    users = db.query(User).all()

    return users


# 🔹 GET ALL ASSISTANTS OF SHOP (SHOP ADMIN)
@router.get("/assistants")
def get_assistants(db: Session = Depends(get_db), user_id: int = 1):

    admin = db.query(User).filter(User.id == user_id).first()

    if not admin or admin.role != Roles.SHOP_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    assistants = db.query(User).filter(
        User.shop_id == admin.shop_id,
        User.role == Roles.SALES_ASSISTANT,
        User.status == "APPROVED"
    ).all()

    return assistants