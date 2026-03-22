from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app import models
from app.auth import get_current_user

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)

# ==========================
# 🔧 SERIALIZER
# ==========================
def serialize_task(t):
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "start_time": t.start_time.isoformat() if t.start_time else None,
        "end_time": t.end_time.isoformat() if t.end_time else None,
        "time_taken": t.time_taken or 0,
        "github_link": t.github_link
    }


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

    return {"success": True, "data": [serialize_task(t) for t in tasks]}


# ==========================
# GET ALL TASKS (ADMIN)
# ==========================
@router.get("/")
def get_all_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    tasks = db.query(models.Task)\
        .order_by(models.Task.id.desc())\
        .all()

    return {"success": True, "data": [serialize_task(t) for t in tasks]}


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
        return {"success": False, "message": "Already started"}

    task.status = "In Progress"
    task.start_time = datetime.now(timezone.utc)

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
        return {"success": False, "message": "Start task first"}

    if task.status == "Completed":
        return {"success": False, "message": "Already completed"}

    task.status = "Completed"
    task.end_time = datetime.now(timezone.utc)

    # 🔥 SAFE TIME CALC
    start = task.start_time
    end = task.end_time

    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)

    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    task.time_taken = (end - start).total_seconds()

    # 🔔 NOTIFY ADMINS
    admins = db.query(models.User)\
        .filter(models.User.role == "ADMIN")\
        .all()

    for admin in admins:
        db.add(models.Notification(
            message=f"{current_user.name} completed task: {task.title}",
            user_id=admin.id,
            sender_id=current_user.id,
            is_read=False,
            created_at=datetime.utcnow()
        ))

    db.commit()

    return {"success": True, "message": "Task completed"}


# ==========================
# ASSIGN TASK (ADMIN)
# ==========================
@router.post("/assign-task")
def assign_task(
    data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    title = data.get("title")
    owner_id = data.get("owner_id")

    if not title or not owner_id:
        raise HTTPException(status_code=400, detail="Missing fields")

    task = models.Task(
        title=title,
        description=data.get("description"),
        owner_id=owner_id,
        assigned_by_id=current_user.id,
        status="Pending",
        github_link=data.get("github_link"),
        created_at=datetime.utcnow()
    )

    db.add(task)

    # 🔔 notify user
    db.add(models.Notification(
        message=f"New task assigned: {title}",
        user_id=owner_id,
        sender_id=current_user.id,
        is_read=False,
        created_at=datetime.utcnow()
    ))

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
        "data": [
            {
                "id": n.id,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None
            }
            for n in notifications
        ]
    }


# ==========================
# MARK AS READ
# ==========================
@router.put("/notifications/read")
def mark_notifications_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db.query(models.Notification)\
        .filter(
            models.Notification.user_id == current_user.id,
            models.Notification.is_read == False
        )\
        .update({"is_read": True})

    db.commit()

    return {"success": True, "message": "Marked as read"}

# ==========================
# 📊 USER DASHBOARD SUMMARY
# ==========================
@router.get("/my-dashboard")
def get_my_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    tasks = db.query(models.Task)\
        .filter(models.Task.owner_id == current_user.id)\
        .all()

    assigned = len(tasks)

    completed = len([t for t in tasks if t.status == "Completed"])
    in_progress = len([t for t in tasks if t.status == "In Progress"])

    total_seconds = sum([t.time_taken or 0 for t in tasks])
    total_hours = round(total_seconds / 3600, 2)

    return {
        "success": True,
        "data": {
            "name": current_user.name,
            "assigned": assigned,
            "completed": completed,
            "in_progress": in_progress,
            "hours": total_hours
        }
    }