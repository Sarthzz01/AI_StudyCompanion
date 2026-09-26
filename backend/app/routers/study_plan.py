from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.study_plan import StudyPlanResponse, StudyPlanTaskOut
from app.services.deps import get_current_user
from app.services.study_plan_service import study_plan_service

router = APIRouter(prefix="/api/study-plan", tags=["study-plan"])


@router.get("", response_model=StudyPlanResponse)
def get_daily_study_plan(
    target_minutes: int = Query(60, ge=15, le=360, description="Available study time budget in minutes"),
    force: bool = Query(False, description="Force regenerate plan tasks for today"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve today's personalized study plan, time-budgeted to student available study hours.
    Combines due spaced revisions, weak topic remediation, and adaptive priorities.
    """
    plan = study_plan_service.get_or_generate_plan(
        db=db,
        user_id=current_user.id,
        target_minutes=target_minutes,
        force_regenerate=force
    )
    return StudyPlanResponse(**plan)


@router.post("/{id}/complete", response_model=StudyPlanTaskOut)
def complete_study_plan_task(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a daily study plan task as completed.
    Logs study session time and increments user study progress.
    """
    completed_task = study_plan_service.complete_task(
        db=db,
        user_id=current_user.id,
        task_id=id
    )
    if not completed_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study plan task with ID {id} not found."
        )
    return StudyPlanTaskOut(**completed_task)
