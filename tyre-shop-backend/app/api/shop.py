from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.deps import get_db
from app.models.user import User
from app.models.shop import Shop
from app.models.join_request import JoinRequest
from app.schemas.shop import JoinShopRequest
from app.core.constants import RequestStatus, Roles

from app.core.dependencies import get_current_user
from app.core.permissions import require_shop_admin

router = APIRouter(tags=["Shop"])


# 🔹 REQUEST JOIN (Sales Assistant)
@router.post("/request-join")
def request_join(
    data: JoinShopRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = current_user

    if user.shop_id:
        raise HTTPException(status_code=400, detail="Already assigned to a shop")

    shop = db.query(Shop).filter(Shop.shop_code == data.shop_code).first()

    if not shop:
        raise HTTPException(status_code=404, detail="Invalid shop code")

    # 🔥 prevent duplicate active request
    existing = db.query(JoinRequest).filter(
        JoinRequest.user_id == user.id,
        JoinRequest.status == RequestStatus.PENDING
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Pending request already exists")

    request = JoinRequest(
        user_id=user.id,
        shop_id=shop.id
    )

    db.add(request)
    db.commit()

    return {"message": "Join request sent"}


# 🔹 LIST REQUESTS (SHOP ADMIN ONLY)
@router.get("/join-requests")
def get_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_shop_admin(current_user)

    # 🔥 cleanup expired
    db.query(JoinRequest).filter(
        JoinRequest.expires_at < datetime.utcnow(),
        JoinRequest.status == RequestStatus.PENDING
    ).delete()

    db.commit()

    requests = db.query(JoinRequest).filter(
        JoinRequest.shop_id == current_user.shop_id,
        JoinRequest.status == RequestStatus.PENDING
    ).all()

    return requests


# 🔹 APPROVE
@router.post("/approve-request/{request_id}")
def approve_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_shop_admin(current_user)

    req = db.query(JoinRequest).filter(JoinRequest.id == request_id).first()

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    # 🔐 shop isolation
    if req.shop_id != current_user.shop_id:
        raise HTTPException(status_code=403, detail="Cannot approve other shop requests")

    user = db.query(User).filter(User.id == req.user_id).first()

    user.shop_id = current_user.shop_id
    user.status = RequestStatus.APPROVED

    req.status = RequestStatus.APPROVED

    db.commit()

    return {"message": "User approved"}


# 🔹 REJECT
@router.post("/reject-request/{request_id}")
def reject_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_shop_admin(current_user)

    req = db.query(JoinRequest).filter(JoinRequest.id == request_id).first()

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    # 🔐 shop isolation
    if req.shop_id != current_user.shop_id:
        raise HTTPException(status_code=403, detail="Cannot reject other shop requests")

    req.status = RequestStatus.REJECTED

    db.commit()

    return {"message": "Request rejected"}