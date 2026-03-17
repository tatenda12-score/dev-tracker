from app import models
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas
from app.auth import hash_password, verify_password, create_access_token
from fastapi import HTTPException
from app.auth import get_current_user
from fastapi import Query
from fastapi import Depends, HTTPException, Query
from app.schemas import BaseResponse, UserOut
from app.auth import get_current_user
from app.models import User, Notification

router = APIRouter(prefix="/users", tags=["Users"])


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", status_code=201)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    try:
        new_user = models.User(
            name=user.name,
            email=user.email,
            password_hash=hash_password(user.password),
            role="USER"
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except Exception as e:
        db.rollback()
        print("ERROR DURING REGISTER:", str(e))  # 👈 THIS WILL SHOW REAL ERROR IN RENDER LOGS
        raise HTTPException(status_code=500, detail="Registration failed")

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
from fastapi.security import OAuth2PasswordRequestForm


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    # find user by email
    db_user = db.query(models.User).filter(
        models.User.email == form_data.username
    ).first()

    # check if user exists
    if not db_user:
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials"
        )

    # verify password
    if not verify_password(form_data.password, db_user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials"
        )

    # create token
    access_token = create_access_token(
        data={
            "sub": db_user.email,
            "role": db_user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
    
@router.get(
    "/me",
    response_model=BaseResponse[UserOut]
)
def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> BaseResponse[UserOut]:

    user = db.query(models.User).filter(
        models.User.email == current_user.email
    ).first()

    return BaseResponse(
        success=True,
        data=UserOut.model_validate(user),
        message="User retrieved successfully",
    )
    
@router.patch("/promote/{user_id}")
def promote_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Only ADMIN can promote
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only ADMIN can promote users"
        )

    user_to_promote = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user_to_promote:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user_to_promote.role == "ADMIN":
        return {"message": "User is already ADMIN"}

    user_to_promote.role = "ADMIN"

    db.commit()
    db.refresh(user_to_promote)

    return {
    "success": True,
    "data": {
        "user_id": user_to_promote.id,
        "new_role": user_to_promote.role
    },
    "message": "User promoted successfully"
}
    
from app.schemas import BaseResponse, PaginatedData, UserOut
@router.get(
    "/",
    response_model=BaseResponse[PaginatedData[UserOut]]
)
def list_users(
skip: int = Query(0, ge=0),
limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> BaseResponse[PaginatedData[UserOut]]:
    
    # Only ADMIN can view users
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only ADMIN can view users"
        )

    # Get total count
    total = db.query(models.User).count()

    # Apply pagination
    users = (
        db.query(models.User)
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Return structured response
    return BaseResponse(
        success=True,
        data=PaginatedData(
            items=[UserOut.model_validate(user) for user in users],
            total=total,
            skip=skip,
            limit=limit,
        ),
        message="Users retrieved successfully",
    )
    
@router.get("/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Notification)\
        .filter(Notification.user_id == current_user.id)\
        .order_by(Notification.created_at.desc())\
        .all()
