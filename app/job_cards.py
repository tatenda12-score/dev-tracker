from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models import JobCard, JobUpdate, User, Notification
from app.auth import get_current_user

router = APIRouter(prefix="/job-cards", tags=["Job Cards"])


# ==========================
# 🔧 HELPER: SERIALIZE JOB
# ==========================
def serialize_job(j):
    return {
        "id": j.id,
        "title": j.title,
        "description": j.description,
        "status": j.status,
        "owner_id": j.owner_id,
        "assigned_by_id": j.assigned_by_id,
        "created_at": j.created_at.isoformat() if j.created_at else None,
        "opened_at": j.opened_at.isoformat() if j.opened_at else None,
        "closed_at": j.closed_at.isoformat() if j.closed_at else None,
        "duration": j.duration,
        "github_link": j.github_link
    }


# ==========================
# GET JOB CARDS
# ==========================
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
        "data": [serialize_job(j) for j in jobs]
    }


# ==========================
# CREATE JOB CARD (ADMIN)
# ==========================
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
        created_at=datetime.utcnow()
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # 🔔 notify user
    notification = Notification(
        message=f"New job assigned: {title}",
        user_id=owner_id,
        sender_id=current_user.id,
        is_read=False,
        created_at=datetime.utcnow()
    )

    db.add(notification)
    db.commit()

    return {
        "success": True,
        "message": "Job card created",
        "data": serialize_job(job)
    }


# ==========================
# OPEN JOB (USER)
# ==========================
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
    job.opened_at = datetime.now(timezone.utc)

    db.commit()

    return {"success": True, "message": "Job started"}


# ==========================
# ADD UPDATE (USER)
# ==========================
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

    if job.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if job.status != "Open":
        raise HTTPException(status_code=400, detail="Job must be open")

    message = data.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Message required")

    update = JobUpdate(
        job_id=job_id,
        message=message,
        created_at=datetime.now(timezone.utc)
    )

    db.add(update)
    db.commit()

    return {"success": True, "message": "Update added"}


# ==========================
# CLOSE JOB (USER)
# ==========================
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

    if job.status != "Open":
        raise HTTPException(status_code=400, detail="Job must be open")

    job.closed_at = datetime.now(timezone.utc)
    job.status = "Closed"

    if job.opened_at:
        job.duration = (job.closed_at - job.opened_at).total_seconds()

    # 🔔 notify admins
    admins = db.query(User).filter(User.role == "ADMIN").all()

    for admin in admins:
        notification = Notification(
            message=f"{current_user.name} closed job: {job.title}",
            user_id=admin.id,
            sender_id=current_user.id,
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.add(notification)

    db.commit()

    return {"success": True, "message": "Job closed"}


# ==========================
# GET JOB WITH UPDATES
# ==========================
@router.get("/{job_id}")
def get_job_with_updates(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(JobCard).filter(JobCard.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 🔒 Only owner or admin
    if current_user.role != "ADMIN" and job.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    updates = db.query(JobUpdate)\
        .filter(JobUpdate.job_id == job_id)\
        .order_by(JobUpdate.created_at.asc())\
        .all()

    return {
        "success": True,
        "data": {
            "job": serialize_job(job),
            "updates": [
                {
                    "message": u.message,
                    "created_at": u.created_at.isoformat() if u.created_at else None
                }
                for u in updates
            ]
        }
    }
    
    
    @router.put("/{job_id}/start")
    def start_job(job_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):

        job = db.query(models.JobCard).filter(models.JobCard.id == job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job.status = "Open"
        job.opened_at = datetime.utcnow()

        db.commit()

        return {
            "success": True,
            "message": "Job started"
        }