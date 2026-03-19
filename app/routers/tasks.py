from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app import models
from app.auth import get_current_user
from app.models import Task

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
def get_tasks_for_user(user_id: int, db: Session = Depends(get_db)):

    tasks = db.query(models.Task).filter(
        models.Task.owner_id == user_id
    ).all()

    return {
        "success": True,
        "data": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "start_time": t.start_time.isoformat() if t.start_time else None,
                "end_time": t.end_time.isoformat() if t.end_time else None,
                "time_taken": t.time_taken
            }
            for t in tasks
        ]
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

    if task.status == "In Progress":
        return {"success": False, "message": "Task already started"}

    task.status = "In Progress"
    task.start_time = datetime.now(timezone.utc)  # ✅ FIXED

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

    if not task.start_time:
        return {"success": False, "message": "Task not started yet"}

    task.status = "Completed"
    task.end_time = datetime.now(timezone.utc)  # ✅ FIXED

    # calculate duration safely
    # normalize both datetimes
    start = task.start_time
    end = task.end_time

    if start.tzinfo is None:
       start = start.replace(tzinfo=timezone.utc)

    if end.tzinfo is None: 
      end = end.replace(tzinfo=timezone.utc)

    task.time_taken = (end - start).total_seconds()

    # ==========================
    # 🔔 NOTIFY ADMIN
    # ==========================
    admin_users = db.query(models.User).filter(models.User.role == "ADMIN").all()

    for admin in admin_users:
        notification = models.Notification(
            message=f"{current_user.name} completed task: {task.title}",
            user_id=admin.id,
            sender_id=current_user.id
        )
        db.add(notification)

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
        status="Pending"
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

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