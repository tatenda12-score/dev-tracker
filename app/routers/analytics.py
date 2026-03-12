from app.services.analytics_service import calculate_total_hours
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db
from app import models
from app.auth import get_current_user

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

# 🔹 1. Total Hours for Current User
@router.get("/total-hours")
def total_hours(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    total_hours = calculate_total_hours(db, current_user.id)

    return {
        "success": True,
        "data": {
            "user": current_user.email,
            "total_hours": total_hours
        },
        "message": "Total hours retrieved successfully"
    }


# 🔹 2. Weekly Summary for Current User
@router.get("/weekly-summary")
def weekly_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    one_week_ago = datetime.utcnow() - timedelta(days=7)

    total = db.query(func.sum(models.Task.hours_spent)) \
        .filter(models.Task.owner_id == current_user.id) \
        .filter(models.Task.completed_at >= one_week_ago) \
        .scalar()

    return {
    "success": True,
    "data": {
        "week_start": one_week_ago.date(),
        "total_hours": total or 0
    },
    "message": "Weekly summary retrieved successfully"
}


# 🔹 3. Leaderboard (All Users Ranked)
from fastapi import HTTPException

@router.get("/leaderboard")
def leaderboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only ADMIN can view leaderboard")

    results = db.query(
        models.User.email,
        func.sum(models.Task.hours_spent).label("total_hours")
    ).join(models.Task) \
     .group_by(models.User.email) \
     .order_by(func.sum(models.Task.hours_spent).desc()) \
     .all()

    leaderboard_data = []

    for index, (email, total) in enumerate(results, start=1):
        leaderboard_data.append({
            "rank": index,
            "user": email,
            "total_hours": total
        })

    return {
    "success": True,
    "data": leaderboard_data,
    "message": "Leaderboard retrieved successfully"
}

@router.get("/whoami")
def whoami(current_user: models.User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "role": current_user.role
    }
    
@router.get("/productivity-score")
def productivity_score(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    one_week_ago = datetime.utcnow() - timedelta(days=7)

    total = db.query(func.sum(models.Task.hours_spent)) \
        .filter(models.Task.owner_id == current_user.id) \
        .filter(models.Task.completed_at >= one_week_ago) \
        .scalar()

    total_hours = total or 0
    score = round(total_hours / 7, 2)

    return {
    "success": True,
    "data": {
        "user": current_user.email,
        "weekly_hours": total_hours,
        "productivity_score": score
    },
    "message": "Productivity score calculated successfully"
}