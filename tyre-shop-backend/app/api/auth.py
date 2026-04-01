from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password, create_access_token
from app.core.constants import Roles
from app.schemas.auth import LoginRequest

router = APIRouter(tags=["Auth"])


# -------------------------
# REGISTER
# -------------------------
@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Normalize email
    email = user.email.lower()

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    new_user = User(
        name=user.name,
        email=email,
        password=hash_password(user.password),
        dob=user.dob,
        role=Roles.SALES_ASSISTANT,
        status="PENDING"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully. Awaiting approval."}


# -------------------------
# LOGIN (JWT TOKEN)
# -------------------------
@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Normalize email (important for consistency)
    email = request.email.lower()

    user = db.query(User).filter(User.email == email).first()

    # Validate credentials
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(request.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Block only rejected users (business decision)
    if user.status == "REJECTED":
        raise HTTPException(status_code=403, detail="Account rejected")

    # Create JWT token (includes status for authorization layer)
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "role": user.role,
            "shop_id": user.shop_id,
            "status": user.status,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "role": user.role,
            "status": user.status,
            "shop_id": user.shop_id
        },
    }



# -------------------------
# LOGIN (JWT TOKEN) - Deadlock condition was being hit
# -------------------------
# @router.post("/login")
# def login(
#     form_data: OAuth2PasswordRequestForm = Depends(),
#     db: Session = Depends(get_db)
# ):
#     # OAuth2 uses "username" field → we treat it as email
#     email = form_data.username.lower()

#     db_user = db.query(User).filter(User.email == email).first()

#     # Validate credentials
#     if not db_user or not verify_password(form_data.password, db_user.password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid credentials"
#         )

#     # Check if user is approved
#     if db_user.status != "APPROVED":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="User not approved yet"
#         )

#     # Create JWT token
#     access_token = create_access_token({
#         "sub": db_user.email,
#         "user_id": db_user.id,
#         "role": db_user.role
#     })

#     return {
#         "access_token": access_token,
#         "token_type": "bearer"
#     }

# ----------------------
# Login Form
# ----------------------
@router.post("/login-form")
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    email = form_data.username.lower()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.status == "REJECTED":
        raise HTTPException(status_code=403, detail="Account rejected")

    access_token = create_access_token(
        data={
            "user_id": user.id,
            "role": user.role,
            "shop_id": user.shop_id,
            "status": user.status,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
