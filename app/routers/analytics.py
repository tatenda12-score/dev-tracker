from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db
from app import models
from app.auth import get_current_user
from app.services.analytics_service import calculate_total_hours

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

# ==========================
# 1. TOTAL HOURS (USER)
# ==========================
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
            "total_hours": total_hours or 0
        },
        "message": "Total hours retrieved successfully"
    }


# ==========================
# 2. WEEKLY SUMMARY
# ==========================
@router.get("/weekly-summary")
def weekly_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    one_week_ago = datetime.utcnow() - timedelta(days=7)

    total = db.query(func.sum(models.Task.hours_spent)) \
        .filter(models.Task.owner_id == current_user.id) \
        .filter(models.Task.completed_at != None) \
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


# ==========================
# 3. LEADERBOARD (ADMIN)
# ==========================
@router.get("/leaderboard")
def leaderboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only ADMIN can view leaderboard")

    results = db.query(
        models.User.email,
        func.coalesce(func.sum(models.Task.hours_spent), 0).label("total_hours")
    ).join(models.Task, models.Task.owner_id == models.User.id) \
     .group_by(models.User.email) \
     .order_by(func.sum(models.Task.hours_spent).desc()) \
     .all()

    leaderboard_data = []

    for index, (email, total) in enumerate(results, start=1):
        leaderboard_data.append({
            "rank": index,
            "user": email,
            "total_hours": float(total or 0)
        })

    return {
        "success": True,
        "data": leaderboard_data,
        "message": "Leaderboard retrieved successfully"
    }


# ==========================
# 4. WHO AM I
# ==========================
@router.get("/whoami")
def whoami(current_user: models.User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "role": current_user.role
    }


# ==========================
# 5. PRODUCTIVITY SCORE
# ==========================
@router.get("/productivity-score")
def productivity_score(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    one_week_ago = datetime.utcnow() - timedelta(days=7)

    total = db.query(func.sum(models.Task.hours_spent)) \
        .filter(models.Task.owner_id == current_user.id) \
        .filter(models.Task.completed_at != None) \
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


# ==========================
# 6. DASHBOARD STATS (ADMIN UI 🔥)
# ==========================
@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    total_jobs = db.query(models.JobCard).count()

    active_tasks = db.query(models.Task).filter(
        models.Task.status == "In Progress"
    ).count()

    completed_tasks = db.query(models.Task).filter(
        models.Task.status == "Completed"
    ).count()

    overdue_tasks = db.query(models.Task).filter(
        models.Task.status == "Overdue"
    ).count()

    return {
        "total_jobs": total_jobs,
        "active_tasks": active_tasks,
        "completed_tasks": completed_tasks,
        "overdue_tasks": overdue_tasks
    }


# ==========================
# 7. CHART DATA (REAL 🔥)
# ==========================
@router.get("/charts")
def get_charts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    # Pie data
    completed = db.query(models.Task).filter(models.Task.status == "Completed").count()
    in_progress = db.query(models.Task).filter(models.Task.status == "In Progress").count()
    pending = db.query(models.Task).filter(models.Task.status == "Pending").count()

    # Bar data (last 5 days)
    today = datetime.utcnow()
    days = []

    for i in range(5):
        day = today - timedelta(days=i)

        count = db.query(models.Task).filter(
            models.Task.created_at != None,
            models.Task.created_at >= day.replace(hour=0, minute=0, second=0),
            models.Task.created_at <= day.replace(hour=23, minute=59, second=59)
        ).count()

        days.append(count)

    days.reverse()

    return {
        "pie": [completed, in_progress, pending],
        "bar": days
    }