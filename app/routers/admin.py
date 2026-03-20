from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Task, Notification, User, JobCard
from app.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==========================
# AUTH CHECK
# ==========================
def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ==========================
# GET ALL USERS (FOR DASHBOARD)
# ==========================
@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    users = db.query(User).all()
    return users


# ==========================
# ASSIGN TASK
# ==========================
@router.post("/assign-task")
def assign_task(
    data: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    title = data.get("title")
    description = data.get("description")
    owner_id = data.get("owner_id")

    if not title or not owner_id:
        raise HTTPException(status_code=400, detail="Missing required fields")

    new_task = Task(
        title=title,
        description=description,
        owner_id=owner_id,
        assigned_by_id=admin.id,
        status="Pending",
        created_at=datetime.utcnow()
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # Notification
    notification = Notification(
        message=f"New task assigned: {title}",
        user_id=owner_id,
        sender_id=admin.id,
        created_at=datetime.utcnow()
    )

    db.add(notification)
    db.commit()

    return {"message": "Task assigned successfully"}


# ==========================
# CREATE JOB CARD
# ==========================
@router.post("/create-job")
def create_job_card(
    data: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    title = data.get("title")
    description = data.get("description")
    owner_id = data.get("owner_id")

    if not title or not owner_id:
        raise HTTPException(status_code=400, detail="Missing required fields")

    new_job = JobCard(
        title=title,
        description=description,
        owner_id=owner_id,
        created_by_id=admin.id,
        status="Pending",
        created_at=datetime.utcnow()
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # Notification
    notification = Notification(
        message=f"New job assigned: {title}",
        user_id=owner_id,
        sender_id=admin.id,
        created_at=datetime.utcnow()
    )

    db.add(notification)
    db.commit()

    return {"message": "Job card created successfully"}


# ==========================
# GET NOTIFICATIONS
# ==========================
@router.get("/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    notifications = db.query(Notification).order_by(Notification.id.desc()).all()
    return notifications


# ==========================
# MARK NOTIFICATIONS AS READ
# ==========================
@router.put("/notifications/read")
def mark_notifications_read(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    db.query(Notification).update({"is_read": True})
    db.commit()
    return {"message": "Notifications marked as read"}