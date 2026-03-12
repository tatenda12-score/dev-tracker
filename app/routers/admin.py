from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Task, Notification, User
from app.auth import get_current_user
from app.models import User, Task

router = APIRouter(prefix="/admin", tags=["Admin"])

def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    users = db.query(User).all()
    tasks = db.query(Task).all()

    return {
        "users": users,
        "tasks": tasks
    }
    
@router.post("/assign-task")
def assign_task(
    title: str,
    description: str,
    owner_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    new_task = Task(
        title=title,
        description=description,
        owner_id=owner_id,
        assigned_by_id=admin.id,
        status="pending"
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # CREATE NOTIFICATION
    notification = Notification(
        message=f"New task assigned: {title}",
        user_id=owner_id,
        sender_id=admin.id
    )

    db.add(notification)
    db.commit()

    return {"message": "Task assigned successfully"}

    # Create notification
    notification = Notification(
        message=f"You have been assigned a new task: {title}",
        user_id=owner_id,
        sender_id=admin.id
    )

    db.add(notification)
    db.commit()

    return {"message": "Task assigned successfully"}