from fastapi import HTTPException, status
from app.models.user import User
from app.core.constants import Roles


# -------------------------
# ROLE CHECKS
# -------------------------

def require_admin(user: User):
    if user.role != Roles.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


def require_shop_admin(user: User):
    if user.role != Roles.SHOP_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Shop admin access required"
        )
    return user


def require_sales_assistant(user: User):
    if user.role != Roles.SALES_ASSISTANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sales assistant access required"
        )
    return user


# -------------------------
# SHOP ISOLATION
# -------------------------

def require_same_shop(user: User, shop_id: int):
    if user.shop_id != shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this shop is not allowed"
        )