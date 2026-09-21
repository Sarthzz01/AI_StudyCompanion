from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.learner import LearnerModel
from app.schemas.recommendation import RecommendationOut, DailyRecommendationResponse
from app.services.deps import get_current_user
from app.services.adaptive_engine import adaptive_engine
from app.services.ai_service import ai_service

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("", response_model=List[RecommendationOut])
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all personalized adaptive recommendations ranked by priority.
    Considers topic mastery, quiz accuracy, flashcard performance, forgetting decay,
    and recent error patterns.
    """
    recs = adaptive_engine.get_all_recommendations(db, current_user.id)
    return [RecommendationOut(**r) for r in recs]


@router.get("/today", response_model=DailyRecommendationResponse)
def get_today_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve curated daily recommendations for today's study session,
    along with grounded AI pedagogical focus advice and overdue revision count.
    """
    today_recs = adaptive_engine.get_today_recommendations(db, current_user.id, limit=4)
    now = datetime.utcnow()

    # Calculate count of topics currently overdue for review
    overdue_count = (
        db.query(LearnerModel)
        .filter(
            LearnerModel.user_id == current_user.id,
            (LearnerModel.next_review <= now) | (LearnerModel.recall_reliability < 0.60)
        )
        .count()
    )

    # Generate grounded AI advice
    study_tip = ai_service.generate_recommendations_tip(today_recs)

    return DailyRecommendationResponse(
        date=now.strftime("%Y-%m-%d"),
        recommendations=[RecommendationOut(**r) for r in today_recs],
        ai_study_tip=study_tip,
        total_pending_revisions=overdue_count
    )
