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