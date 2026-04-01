from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.deps import get_db
from app.models.user import User
from app.models.shop import Shop
from app.models.join_request import JoinRequest
from app.schemas.shop import JoinShopRequest
from app.core.constants import RequestStatus, Roles

router = APIRouter()


# 🔹 REQUEST JOIN
@router.post("/request-join")
def request_join(
    data: JoinShopRequest,
    db: Session = Depends(get_db),
    user_id: int = 1  # temp
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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
    user_id: int = 1
):
    admin = db.query(User).filter(User.id == user_id).first()

    if not admin or admin.role != Roles.SHOP_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 🔥 cleanup expired
    db.query(JoinRequest).filter(
        JoinRequest.expires_at < datetime.utcnow(),
        JoinRequest.status == RequestStatus.PENDING
    ).delete()

    db.commit()

    requests = db.query(JoinRequest).filter(
        JoinRequest.shop_id == admin.shop_id,
        JoinRequest.status == RequestStatus.PENDING
    ).all()

    return requests


# 🔹 APPROVE
@router.post("/approve-request/{request_id}")
def approve_request(
    request_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1
):
    admin = db.query(User).filter(User.id == user_id).first()

    if not admin or admin.role != Roles.SHOP_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    req = db.query(JoinRequest).filter(JoinRequest.id == request_id).first()

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.shop_id != admin.shop_id:
        raise HTTPException(status_code=403, detail="Cannot approve other shop requests")

    user = db.query(User).filter(User.id == req.user_id).first()

    user.shop_id = admin.shop_id
    user.status = RequestStatus.APPROVED

    req.status = RequestStatus.APPROVED

    db.commit()

    return {"message": "User approved"}


# 🔹 REJECT
@router.post("/reject-request/{request_id}")
def reject_request(
    request_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1
):
    admin = db.query(User).filter(User.id == user_id).first()

    if not admin or admin.role != Roles.SHOP_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    req = db.query(JoinRequest).filter(JoinRequest.id == request_id).first()

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.shop_id != admin.shop_id:
        raise HTTPException(status_code=403, detail="Cannot reject other shop requests")

    req.status = RequestStatus.REJECTED

    db.commit()

    return {"message": "Request rejected"}