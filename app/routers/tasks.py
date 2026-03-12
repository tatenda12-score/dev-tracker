from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from datetime import datetime
from app.schemas import BaseResponse, PaginatedData, TaskOut
from fastapi import Depends, Query
from app.models import Task
router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)

# Create Task (USER only)
@router.post("/")
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "USER":
        raise HTTPException(status_code=403, detail="Only USERS can create tasks")

    new_task = models.Task(
        title=task.title,
        description=task.description,
        github_link=task.github_link,
        hours_spent=task.hours_spent,
        completed_at=datetime.utcnow(),
        owner_id=current_user.id
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


# Get My Tasks
@router.get(
    "/my-tasks",
    response_model=BaseResponse[PaginatedData[TaskOut]]
)
def get_my_tasks(
skip: int = Query(0, ge=0),
limit: int = Query(10, ge=1, le=100),
min_hours: int | None = Query(None, ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> BaseResponse[PaginatedData[TaskOut]]:

    # Base query
    query = db.query(models.Task).filter(
        models.Task.owner_id == current_user.id
    )

    # Optional filtering
    if min_hours is not None:
        query = query.filter(
            models.Task.hours_spent >= min_hours
        )

    # Count AFTER filtering
    total = query.count()

    # Sorting + pagination
    tasks = (
        query.order_by(models.Task.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return BaseResponse(
        success=True,
        data=PaginatedData(
            items=[TaskOut.model_validate(task) for task in tasks],
            total=total,
            skip=skip,
            limit=limit,
        ),
        message="Tasks retrieved successfully",
    )
@router.get("/user/{user_id}")
def get_tasks_for_user(user_id: int, db: Session = Depends(get_db)):

    tasks = (
        db.query(Task)
        .filter(Task.owner_id == user_id)
        .order_by(Task.completed_at.desc())
        .all()
    )

    return {
        "success": True,
        "data": tasks
    }
    
@router.get("/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    notifications = db.query(models.Notification)\
        .filter(models.Notification.user_id == current_user.id)\
        .filter(models.Notification.is_read == False)\
        .order_by(models.Notification.created_at.desc())\
        .all()

    # mark them as read
    for n in notifications:
        n.is_read = True

    db.commit()

    return notifications  

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
        github_link=data.get("github_link"),
        hours_spent=data["hours_spent"],
        completed_at=datetime.utcnow(),
        owner_id=data["owner_id"]
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

    return {"success": True}

    # create notification
    notification = models.Notification(
        message=f"New task assigned: {task.title}",
        user_id=owner_id,
        sender_id=current_user.id
    )

    db.add(notification)
    db.commit()

    return {"success": True, "message": "Task assigned"}