from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.database import SessionLocal
from app import models, schemas
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.schemas import BaseResponse, PaginatedData, UserOut
from app.models import User

router = APIRouter(prefix="/users", tags=["Users"])


# ==========================
# DB DEPENDENCY
# ==========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================
# REGISTER USER
# ==========================
@router.post("/register", status_code=201)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    new_user = models.User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password),
        role="USER"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "success": True,
        "data": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role
        },
        "message": "User created successfully"
    }


# ==========================
# LOGIN (FIXED FOR FRONTEND)
# ==========================
@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    db_user = db.query(models.User).filter(
        models.User.email == form_data.username
    ).first()

    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(form_data.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(
        data={
            "sub": db_user.email,
            "role": db_user.role
        }
    )

    # ✅ IMPORTANT: MATCH FRONTEND EXPECTATION
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "name": db_user.name,
            "email": db_user.email,
            "role": db_user.role
        }
    }


# ==========================
# GET CURRENT USER
# ==========================
@router.get("/me")
def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role
        }
    }


# ==========================
# LIST USERS (ADMIN)
# ==========================
@router.get("/")
def list_users(
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    users = db.query(models.User).offset(skip).limit(limit).all()

    return {
        "success": True,
        "data": users
    }


# ==========================
# PROMOTE USER
# ==========================
@router.patch("/promote/{user_id}")
def promote_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = "ADMIN"
    db.commit()

    return {
        "success": True,
        "message": "User promoted"
    }