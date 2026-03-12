
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models


def calculate_total_hours(db: Session, user_id: int):
    total = db.query(func.sum(models.Task.hours_spent)) \
        .filter(models.Task.owner_id == user_id) \
        .scalar()

    return total or 0