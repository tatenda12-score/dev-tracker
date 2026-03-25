from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import timedelta

from app.database import get_db
from app import models
from app.auth import get_current_user
from app.services.analytics_service import calculate_total_hours
from app.time_utils import now_harare

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


def build_user_daily_chart(db: Session, user_id: int, days: int = 7):
    today = now_harare()
    labels = []
    item_counts = []
    hour_totals = []

    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        start_of_day = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = day.replace(hour=23, minute=59, second=59, microsecond=999999)

        tasks_completed = db.query(func.count(models.Task.id)).filter(
            models.Task.owner_id == user_id,
            models.Task.completed_at != None,
            models.Task.completed_at >= start_of_day,
            models.Task.completed_at <= end_of_day
        ).scalar()

        jobs_completed = db.query(func.count(models.JobCard.id)).filter(
            models.JobCard.owner_id == user_id,
            models.JobCard.closed_at != None,
            models.JobCard.closed_at >= start_of_day,
            models.JobCard.closed_at <= end_of_day
        ).scalar()

        hours_completed = db.query(func.coalesce(func.sum(models.Task.hours_spent), 0)).filter(
            models.Task.owner_id == user_id,
            models.Task.completed_at != None,
            models.Task.completed_at >= start_of_day,
            models.Task.completed_at <= end_of_day
        ).scalar()

        job_hours_completed = db.query(func.coalesce(func.sum(models.JobCard.duration), 0)).filter(
            models.JobCard.owner_id == user_id,
            models.JobCard.closed_at != None,
            models.JobCard.closed_at >= start_of_day,
            models.JobCard.closed_at <= end_of_day
        ).scalar()

        labels.append(day.strftime("%a"))
        item_counts.append(int(tasks_completed or 0) + int(jobs_completed or 0))
        total_seconds = float(hours_completed or 0) * 3600 + float(job_hours_completed or 0)
        hour_totals.append(round(total_seconds / 3600, 2))

    return {
        "labels": labels,
        "items": item_counts,
        "hours": hour_totals
    }

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
    one_week_ago = now_harare() - timedelta(days=7)

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
    one_week_ago = now_harare() - timedelta(days=7)

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
# 6. USER CHART DATA
# ==========================
@router.get("/my-charts")
def get_my_charts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    completed = db.query(models.Task).filter(
        models.Task.owner_id == current_user.id,
        models.Task.status == "Completed"
    ).count()
    completed += db.query(models.JobCard).filter(
        models.JobCard.owner_id == current_user.id,
        models.JobCard.status == "Closed"
    ).count()
    in_progress = db.query(models.Task).filter(
        models.Task.owner_id == current_user.id,
        models.Task.status == "In Progress"
    ).count()
    in_progress += db.query(models.JobCard).filter(
        models.JobCard.owner_id == current_user.id,
        models.JobCard.status == "Open"
    ).count()
    pending = db.query(models.Task).filter(
        models.Task.owner_id == current_user.id,
        models.Task.status == "Pending"
    ).count()
    pending += db.query(models.JobCard).filter(
        models.JobCard.owner_id == current_user.id,
        models.JobCard.status == "Pending"
    ).count()

    return {
        "success": True,
        "data": {
            "pie": {
                "labels": ["Completed", "In Progress", "Pending"],
                "data": [completed, in_progress, pending]
            },
            "bar": build_user_daily_chart(db, current_user.id, days=5),
            "line": build_user_daily_chart(db, current_user.id, days=7)
        }
    }


# ==========================
# 7. DASHBOARD STATS (ADMIN UI 🔥)
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
# 8. CHART DATA (REAL 🔥)
# ==========================
@router.get("/charts")
def get_charts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    completed = db.query(models.Task).filter(models.Task.status == "Completed").count()
    in_progress = db.query(models.Task).filter(models.Task.status == "In Progress").count()
    pending = db.query(models.Task).filter(models.Task.status == "Pending").count()

    today = now_harare()
    labels = []
    counts = []

    for i in range(5):
        day = today - timedelta(days=i)
        start_of_day = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = day.replace(hour=23, minute=59, second=59, microsecond=999999)

        count = db.query(models.Task).filter(
            models.Task.created_at != None,
            models.Task.created_at >= start_of_day,
            models.Task.created_at <= end_of_day
        ).count()

        labels.append(day.strftime("%a"))
        counts.append(count)

    labels.reverse()
    counts.reverse()

    return {
        "pie": {
            "labels": ["Completed", "In Progress", "Pending"],
            "data": [completed, in_progress, pending]
        },
        "bar": {
            "labels": labels,
            "data": counts
        }
    }
