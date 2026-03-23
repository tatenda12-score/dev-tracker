from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_db
from app import models, schemas
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


# ==========================
# 🔧 HELPER: SERIALIZE USER
# ==========================
def serialize_user(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }


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
        "data": serialize_user(new_user),
        "message": "User created successfully"
    }


# ==========================
# LOGIN
# ==========================
@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    db_user = db.query(models.User).filter(
        models.User.email == form_data.username
    ).first()

    if not db_user or not verify_password(form_data.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(
        data={
            "sub": db_user.email,
            "role": db_user.role
        }
    )

    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "user": serialize_user(db_user)
        },
        "message": "Login successful"
    }


# ==========================
# GET CURRENT USER
# ==========================
@router.get("/me")
def get_current_user_profile(
    current_user: models.User = Depends(get_current_user)
):
    return {
        "success": True,
        "data": serialize_user(current_user)
    }


# ==========================
# LIST USERS (ADMIN)
# ==========================
@router.get("/")
def list_users(
    skip: int = Query(0),
    limit: int = Query(10),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    query = db.query(models.User)

    if search:
        query = query.filter(models.User.email.contains(search))

    users = query.offset(skip).limit(limit).all()

    return {
        "success": True,
        "data": [serialize_user(u) for u in users]
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

    if user.role == "ADMIN":
        return {"success": False, "message": "User already admin"}

    user.role = "ADMIN"
    db.commit()

    return {
        "success": True,
        "message": f"{user.email} promoted to ADMIN"
    }


# ==========================
# DELETE USER (ADMIN 🔥)
# ==========================
@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {
        "success": True,
        "message": "User deleted"
    }
    
    