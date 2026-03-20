from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app import models


# ==========================
# TOTAL HOURS (FLEXIBLE 🔥)
# ==========================
def calculate_total_hours(
    db: Session,
    user_id: int,
    start_date: datetime = None,
    end_date: datetime = None,
    status: str = None
):
    query = db.query(
        func.coalesce(func.sum(models.Task.hours_spent), 0)
    ).filter(models.Task.owner_id == user_id)

    # 🔥 Optional filters (powerful)
    if start_date:
        query = query.filter(models.Task.completed_at >= start_date)

    if end_date:
        query = query.filter(models.Task.completed_at <= end_date)

    if status:
        query = query.filter(models.Task.status == status)

    total = query.scalar()

    return float(total or 0)