from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.auth import get_current_user
from app.time_utils import ensure_harare, now_harare

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)


def serialize_task(task):
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "start_time": task.start_time.isoformat() if task.start_time else None,
        "end_time": task.end_time.isoformat() if task.end_time else None,
        "time_taken": float(task.time_taken) if task.time_taken else 0,
        "hours_spent": float(task.hours_spent) if task.hours_spent else 0,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "github_link": task.github_link,
        "owner_id": task.owner_id,
        "assigned_by_id": task.assigned_by_id,
    }


def serialize_task_update(update):
    return {
        "id": update.id,
        "message": update.message,
        "created_at": update.created_at.isoformat() if update.created_at else None,
        "author_name": update.author.name if getattr(update, "author", None) else "Unknown",
        "author_role": update.author.role if getattr(update, "author", None) else "USER",
    }


def create_notification(db: Session, user_id: int, sender_id: int | None, message: str):
    db.add(models.Notification(
        message=message,
        user_id=user_id,
        sender_id=sender_id,
        is_read=False,
        created_at=now_harare()
    ))


@router.get("/my-tasks")
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    tasks = db.query(models.Task)\
        .filter(models.Task.owner_id == current_user.id)\
        .order_by(models.Task.id.desc())\
        .all()

    return {"success": True, "data": [serialize_task(task) for task in tasks]}


@router.get("/")
def get_all_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized")

    tasks = db.query(models.Task).order_by(models.Task.id.desc()).all()
    result = []

    for task in tasks:
        owner = db.query(models.User).filter(models.User.id == task.owner_id).first()
        result.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "github_link": task.github_link,
            "owner_name": owner.name if owner else "Unknown",
            "created_at": task.created_at,
            "time_taken": task.time_taken
        })

    return {
        "success": True,
        "data": result
    }


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
    task.start_time = now_harare()

    db.commit()

    return {"success": True, "message": "Task started"}


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
    task.end_time = now_harare()

    start = ensure_harare(task.start_time)
    end = ensure_harare(task.end_time)

    task.time_taken = (end - start).total_seconds()
    task.hours_spent = round(task.time_taken / 3600, 2)
    task.completed_at = task.end_time

    admins = db.query(models.User)\
        .filter(models.User.role == "ADMIN")\
        .all()

    for admin in admins:
        create_notification(
            db,
            admin.id,
            current_user.id,
            f"{current_user.name} completed task: {task.title}"
        )

    db.commit()

    return {"success": True, "message": "Task completed"}


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
        created_at=now_harare()
    )

    db.add(task)
    create_notification(db, owner_id, current_user.id, f"New task assigned: {title}")
    db.commit()

    return {"success": True, "message": "Task assigned successfully"}


@router.post("/update/{task_id}")
def add_task_update(
    task_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if current_user.role != "ADMIN" and task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    message = (data.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message required")

    update = models.TaskUpdate(
        task_id=task_id,
        author_id=current_user.id,
        message=message,
        created_at=now_harare()
    )
    db.add(update)

    if current_user.role == "ADMIN":
        create_notification(db, task.owner_id, current_user.id, f"Admin commented on task: {task.title}")
    else:
        admins = db.query(models.User).filter(models.User.role == "ADMIN").all()
        for admin in admins:
            create_notification(db, admin.id, current_user.id, f"{current_user.name} updated task: {task.title}")

    db.commit()
    db.refresh(update)

    return {
        "success": True,
        "message": "Task update added",
        "data": serialize_task_update(update)
    }


@router.get("/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    notifications = db.query(models.Notification)\
        .filter(models.Notification.user_id == current_user.id)\
        .order_by(models.Notification.created_at.desc())\
        .all()

    unread_count = sum(1 for notification in notifications if not notification.is_read)

    return {
        "success": True,
        "data": [
            {
                "id": notification.id,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat() if notification.created_at else None
            }
            for notification in notifications
        ],
        "meta": {
            "unread_count": unread_count
        }
    }


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


@router.get("/my-dashboard")
def get_my_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    tasks = db.query(models.Task)\
        .filter(models.Task.owner_id == current_user.id)\
        .all()

    assigned = len(tasks)
    completed = len([task for task in tasks if task.status == "Completed"])
    in_progress = len([task for task in tasks if task.status == "In Progress"])

    total_seconds = sum([task.time_taken or 0 for task in tasks])
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


@router.get("/{task_id}")
def get_task_with_updates(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if current_user.role != "ADMIN" and task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    owner = db.query(models.User).filter(models.User.id == task.owner_id).first()
    assigned_by = db.query(models.User).filter(models.User.id == task.assigned_by_id).first()
    updates = db.query(models.TaskUpdate)\
        .filter(models.TaskUpdate.task_id == task_id)\
        .order_by(models.TaskUpdate.created_at.asc())\
        .all()

    return {
        "success": True,
        "data": {
            "task": {
                **serialize_task(task),
                "owner_name": owner.name if owner else "Unknown",
                "assigned_by_name": assigned_by.name if assigned_by else "Unknown",
            },
            "updates": [serialize_task_update(update) for update in updates]
        }
    }
