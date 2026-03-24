from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import JobCard, JobUpdate, User, Notification
from app.auth import get_current_user
from app.time_utils import ensure_harare, now_harare

router = APIRouter(prefix="/job-cards", tags=["Job Cards"])


def serialize_job(job):
    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "status": job.status,
        "owner_id": job.owner_id,
        "assigned_by_id": job.assigned_by_id,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "opened_at": job.opened_at.isoformat() if job.opened_at else None,
        "closed_at": job.closed_at.isoformat() if job.closed_at else None,
        "duration": job.duration,
        "github_link": job.github_link
    }


def serialize_job_update(update):
    return {
        "id": update.id,
        "message": update.message,
        "created_at": update.created_at.isoformat() if update.created_at else None,
        "author_name": "Team update",
        "author_role": "INFO",
    }


def create_notification(db: Session, user_id: int, sender_id: int | None, message: str):
    db.add(Notification(
        message=message,
        user_id=user_id,
        sender_id=sender_id,
        is_read=False,
        created_at=now_harare()
    ))


@router.get("/")
def get_job_cards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "ADMIN":
        jobs = db.query(JobCard).order_by(JobCard.id.desc()).all()
    else:
        jobs = db.query(JobCard)\
            .filter(JobCard.owner_id == current_user.id)\
            .order_by(JobCard.id.desc())\
            .all()

    return {
        "success": True,
        "data": [serialize_job(job) for job in jobs]
    }


@router.post("/")
def create_job_card(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    title = data.get("title")
    owner_id = data.get("owner_id")

    if not title or not owner_id:
        raise HTTPException(status_code=400, detail="Missing required fields")

    job = JobCard(
        title=title,
        description=data.get("description"),
        owner_id=owner_id,
        assigned_by_id=current_user.id,
        status="Pending",
        github_link=data.get("github_link"),
        created_at=now_harare()
    )

    db.add(job)
    create_notification(db, owner_id, current_user.id, f"New job assigned: {title}")
    db.commit()
    db.refresh(job)

    return {
        "success": True,
        "message": "Job created successfully",
        "data": serialize_job(job)
    }


@router.put("/open/{job_id}")
def open_job_card(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(JobCard).filter(JobCard.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if job.status == "Closed":
        raise HTTPException(status_code=400, detail="Job already closed")

    if job.status == "Open":
        return {"success": False, "message": "Already open"}

    job.status = "Open"
    job.opened_at = now_harare()

    db.commit()

    return {"success": True, "message": "Job started"}


@router.post("/update/{job_id}")
def add_job_update(
    job_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(JobCard).filter(JobCard.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if current_user.role != "ADMIN" and job.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if current_user.role != "ADMIN" and job.status != "Open":
        raise HTTPException(status_code=400, detail="Job must be open")

    message = (data.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message required")

    update = JobUpdate(
        job_id=job_id,
        message=message,
        created_at=now_harare()
    )

    db.add(update)

    if current_user.role == "ADMIN":
        create_notification(db, job.owner_id, current_user.id, f"Admin updated job: {job.title}")
    else:
        admins = db.query(User).filter(User.role == "ADMIN").all()
        for admin in admins:
            create_notification(db, admin.id, current_user.id, f"{current_user.name} updated job: {job.title}")

    db.commit()
    db.refresh(update)

    return {
        "success": True,
        "message": "Update added",
        "data": serialize_job_update(update)
    }


@router.put("/close/{job_id}")
def close_job_card(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(JobCard).filter(JobCard.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    job.status = "Closed"
    job.closed_at = now_harare()

    if job.opened_at and job.closed_at:
        opened_at = ensure_harare(job.opened_at)
        closed_at = ensure_harare(job.closed_at)
        job.duration = (closed_at - opened_at).total_seconds()

    admins = db.query(User).filter(User.role == "ADMIN").all()
    for admin in admins:
        create_notification(db, admin.id, current_user.id, f"{current_user.name} closed job: {job.title}")

    db.commit()
    db.refresh(job)

    return {
        "success": True,
        "message": "Job closed"
    }


@router.get("/{job_id}")
def get_job_with_updates(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(JobCard).filter(JobCard.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if current_user.role != "ADMIN" and job.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    owner = db.query(User).filter(User.id == job.owner_id).first()
    assigned_by = db.query(User).filter(User.id == job.assigned_by_id).first()
    updates = db.query(JobUpdate)\
        .filter(JobUpdate.job_id == job_id)\
        .order_by(JobUpdate.created_at.asc())\
        .all()

    return {
        "success": True,
        "data": {
            "job": {
                **serialize_job(job),
                "owner_name": owner.name if owner else "Unknown",
                "assigned_by_name": assigned_by.name if assigned_by else "Unknown",
            },
            "updates": [serialize_job_update(update) for update in updates]
        }
    }
