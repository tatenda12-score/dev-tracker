from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app import models
from app.auth import get_current_user

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)


# ==========================
# GET MY TASKS (USER)
# ==========================
@router.get("/my-tasks")
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    tasks = db.query(models.Task)\
        .filter(models.Task.owner_id == current_user.id)\
        .order_by(models.Task.id.desc())\
        .all()

    return {
        "success": True,
        "data": tasks
    }


# ==========================
# GET TASKS FOR USER (ADMIN)
# ==========================
@router.get("/user/{user_id}")
def get_tasks_for_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    tasks = db.query(models.Task)\
        .filter(models.Task.owner_id == user_id)\
        .order_by(models.Task.id.desc())\
        .all()

    return {
        "success": True,
        "data": tasks
    }


# ==========================
# START TASK
# ==========================
@router.put("/start/{task_id}")
def start_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    task.status = "In Progress"
    task.start_time = datetime.utcnow()

    db.commit()

    return {"success": True, "message": "Task started"}


# ==========================
# COMPLETE TASK
# ==========================
@router.put("/complete/{task_id}")
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    task.status = "Completed"
    task.end_time = datetime.utcnow()

    # calculate time taken
    if task.start_time:
        task.time_taken = (task.end_time - task.start_time).total_seconds()

    db.commit()

    return {"success": True, "message": "Task completed"}


# ==========================
# ASSIGN TASK (ADMIN ONLY)
# ==========================
@router.post("/assign-task")
def assign_task(
    data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admins can assign tasks")

    new_task = models.Task(
        title=data["title"],
        description=data["description"],
        owner_id=data["owner_id"],
        assigned_by_id=current_user.id,
        status="Pending"  # ✅ IMPORTANT
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # create notification
    notification = models.Notification(
        message=f"New task assigned: {data['title']}",
        user_id=data["owner_id"],
        sender_id=current_user.id
    )

    db.add(notification)
    db.commit()

    return {"success": True, "message": "Task assigned"}


# ==========================
# GET NOTIFICATIONS
# ==========================
@router.get("/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    notifications = db.query(models.Notification)\
        .filter(models.Notification.user_id == current_user.id)\
        .order_by(models.Notification.created_at.desc())\
        .all()

    return {
        "success": True,
        "data": notifications
    }