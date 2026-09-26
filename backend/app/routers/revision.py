from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.revision import RevisionItemOut, RevisionDueResponse
from app.services.deps import get_current_user
from app.services.revision_service import revision_service

router = APIRouter(prefix="/api/revision", tags=["revision"])


@router.get("", response_model=List[RevisionItemOut])
def get_all_revision_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all topic revision schedules for the authenticated student,
    including upcoming dates, SM-2 intervals, and recall retention estimates.
    """
    revisions = revision_service.get_all_revisions(db, current_user.id)
    return [RevisionItemOut(**r) for r in revisions]


@router.get("/due", response_model=RevisionDueResponse)
def get_due_revision_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve topics currently due or overdue for spaced repetition review.
    """
    now = datetime.utcnow()
    due_items = revision_service.get_due_revisions(db, current_user.id, now)
    return RevisionDueResponse(
        date=now.strftime("%Y-%m-%d"),
        total_due=len(due_items),
        revisions=[RevisionItemOut(**r) for r in due_items]
    )
