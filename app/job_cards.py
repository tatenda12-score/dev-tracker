from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import JobCard, JobUpdate, User
from app.auth import get_current_user

router = APIRouter(prefix="/job-cards", tags=["Job Cards"])


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
        raise HTTPException(status_code=403, detail="Only admin can create job cards")

    job = JobCard(
        title=data["title"],
        description=data["description"],
        owner_id=data["owner_id"],
        assigned_by_id=current_user.id,
        status="Pending",
        created_at=datetime.utcnow()
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "success": True,
        "message": "Job card created",
        "data": {
            "id": job.id,
            "title": job.title
        }
    }
    
    # ==========================
# OPEN JOB CARD (USER)
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

    # prevent reopening
    if job.status == "Open":
        return {"success": False, "message": "Job already open"}

    job.status = "Open"
    job.opened_at = datetime.utcnow()

    db.commit()

    return {"success": True, "message": "Job started"}

# ==========================
# ADD JOB UPDATE (USER)
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
        raise HTTPException(status_code=400, detail="Job must be open to add updates")

    update = JobUpdate(
        job_id=job_id,
        message=data["message"],
        created_at=datetime.utcnow()
    )

    db.add(update)
    db.commit()

    return {"success": True, "message": "Update added"}

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

    updates = db.query(JobUpdate)\
        .filter(JobUpdate.job_id == job_id)\
        .order_by(JobUpdate.created_at.asc())\
        .all()

    return {
        "job": {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "opened_at": job.opened_at.isoformat() if job.opened_at else None,
            "closed_at": job.closed_at.isoformat() if job.closed_at else None,
            "duration": job.duration
        },
        "updates": [
            {
                "message": u.message,
                "created_at": u.created_at.isoformat()
            }
            for u in updates
        ]
    }
    
    # ==========================
# CLOSE JOB CARD (USER)
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
        raise HTTPException(status_code=400, detail="Job must be open to close")

    job.closed_at = datetime.utcnow()
    job.status = "Closed"

    # calculate duration
    if job.opened_at:
        job.duration = (job.closed_at - job.opened_at).total_seconds()

    db.commit()

    return {"success": True, "message": "Job closed"}

@router.get("/")
def get_my_job_cards(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    jobs = db.query(models.JobCard).filter(
        models.JobCard.owner_id == current_user.id
    ).order_by(models.JobCard.id.desc()).all()

    return {
        "success": True,
        "data": [
            {
                "id": j.id,
                "title": j.title,
                "description": j.description,
                "status": j.status,
                "owner_id": j.owner_id,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "opened_at": j.opened_at.isoformat() if j.opened_at else None,
                "closed_at": j.closed_at.isoformat() if j.closed_at else None,
                "duration": j.duration
            }
            for j in jobs
        ]
    }