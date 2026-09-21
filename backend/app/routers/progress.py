import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.learner import LearnerModel, Progress
from app.models.study import StudySession, Goal, QuizAttempt, QuizAnswer
from app.schemas.progress import (
    ProgressOut,
    TopicProgressOut,
    LearnerModelDetailOut,
    StudySessionCreate,
    StudySessionOut,
    GoalCreate,
    GoalUpdate,
    GoalOut
)
from app.services.deps import get_current_user
from app.services.learner_service import learner_service
from app.services.ai_service import ai_service

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["Progress & Learner Model"])

# =========================================================================
# 1. PROGRESS SUMMARY & TOPIC BREAKDOWN
# =========================================================================

@router.get("/progress", response_model=ProgressOut)
def get_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve comprehensive aggregate student progress matching frontend expectations:
    overall accuracy, questions attempted, study time, topic breakdown, weekly stats,
    performance over time, strong/weak/improving topics.
    """
    summary = learner_service.calculate_progress_summary(db, current_user.id)
    return summary

@router.get("/progress/topics", response_model=List[TopicProgressOut])
def get_topic_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detailed topic-by-topic analytics including mastery, recall reliability,
    difficulty classification, and status badges.
    """
    learner_service.consolidate_learner_models(db, current_user.id)
    learner_models = db.query(LearnerModel).filter(LearnerModel.user_id == current_user.id).all()
    detections = learner_service.detect_topics(learner_models)

    strong_set = set(detections["strong"])
    weak_set = set(detections["weak"])
    improving_set = set(item["topic"] for item in detections["improving"])
    needing_review_set = set(item["topic"] for item in detections["needing_review"])

    results = []
    for lm in learner_models:
        if lm.topic in strong_set:
            topic_status = "strong"
        elif lm.topic in weak_set:
            topic_status = "weak"
        elif lm.topic in improving_set:
            topic_status = "improving"
        elif lm.topic in needing_review_set:
            topic_status = "needs_review"
        else:
            topic_status = "normal"

        results.append(TopicProgressOut(
            id=lm.id,
            topic=lm.topic,
            mastery=round(lm.mastery, 1),
            recall_reliability=round(lm.recall_reliability, 2),
            quiz_accuracy=round(lm.quiz_accuracy, 1),
            flashcard_performance=round(lm.flashcard_performance, 1),
            difficulty=lm.difficulty or "medium",
            status=topic_status,
            last_reviewed=lm.last_reviewed.strftime("%Y-%m-%d %H:%M") if lm.last_reviewed else None,
            next_review=lm.next_review.strftime("%Y-%m-%d") if lm.next_review else None
        ))

    results.sort(key=lambda x: x.mastery, reverse=True)
    return results

# =========================================================================
# 2. LEARNER MODEL & AI SIGNALS
# =========================================================================

@router.get("/learner-model")
def get_learner_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the entire Learner Model state for the authenticated user,
    including topic masteries, recall probabilities, and category detections.
    """
    learner_service.consolidate_learner_models(db, current_user.id)
    learner_models = db.query(LearnerModel).filter(LearnerModel.user_id == current_user.id).all()
    detections = learner_service.detect_topics(learner_models)

    models_data = []
    for lm in learner_models:
        models_data.append({
            "id": lm.id,
            "topic": lm.topic,
            "mastery": round(lm.mastery, 1),
            "recall_reliability": round(lm.recall_reliability, 2),
            "quiz_accuracy": round(lm.quiz_accuracy, 1),
            "flashcard_performance": round(lm.flashcard_performance, 1),
            "difficulty": lm.difficulty,
            "last_reviewed": lm.last_reviewed.strftime("%Y-%m-%d %H:%M") if lm.last_reviewed else None,
            "next_review": lm.next_review.strftime("%Y-%m-%d") if lm.next_review else None,
            "recent_performance": lm.recent_performance_json or []
        })

    avg_mastery = round(sum(lm.mastery for lm in learner_models) / len(learner_models), 1) if learner_models else 0.0
    avg_recall = round(sum(lm.recall_reliability for lm in learner_models) / len(learner_models), 2) if learner_models else 0.5

    return {
        "user_id": current_user.id,
        "topics_tracked": len(learner_models),
        "average_mastery": avg_mastery,
        "average_recall_reliability": avg_recall,
        "strong_topics": detections["strong"],
        "weak_topics": detections["weak"],
        "improving_topics": detections["improving"],
        "topics_needing_review": detections["needing_review"],
        "topics": models_data
    }

@router.get("/learner-model/{topic_id}", response_model=LearnerModelDetailOut)
def get_topic_learner_model(
    topic_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves detailed learner model for a topic (by numeric ID or topic name)
    along with AI diagnostic learning signals grounded in student activity.
    """
    query = db.query(LearnerModel).filter(LearnerModel.user_id == current_user.id)
    if topic_id.isdigit():
        learner = query.filter(LearnerModel.id == int(topic_id)).first()
    else:
        canonical_topic = learner_service.normalize_topic_name(topic_id, db)
        learner = query.filter(LearnerModel.topic.ilike(f"%{canonical_topic}%")).first()
        if not learner:
            learner = query.filter(LearnerModel.topic.ilike(f"%{topic_id}%")).first()

    if not learner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic learner model for '{topic_id}' not found."
        )

    # Fetch recent mistakes for this topic to generate grounded signals
    mistakes = (
        db.query(QuizAnswer)
        .join(QuizAttempt, QuizAttempt.id == QuizAnswer.attempt_id)
        .filter(
            QuizAttempt.user_id == current_user.id,
            QuizAnswer.topic == learner.topic,
            QuizAnswer.is_correct == False
        )
        .order_by(QuizAnswer.created_at.desc())
        .limit(5)
        .all()
    )

    mistake_dicts = [
        {"question_text": m.question_text, "selected": m.selected_option, "correct": m.correct_answer}
        for m in mistakes
    ]

    topic_dict = {
        "mastery": learner.mastery,
        "quiz_accuracy": learner.quiz_accuracy,
        "recall_reliability": learner.recall_reliability,
        "difficulty": learner.difficulty
    }

    signals_data = ai_service.generate_learning_signals(learner.topic, topic_dict, mistake_dicts)

    return LearnerModelDetailOut(
        id=learner.id,
        topic=learner.topic,
        mastery=round(learner.mastery, 1),
        recall_reliability=round(learner.recall_reliability, 2),
        quiz_accuracy=round(learner.quiz_accuracy, 1),
        flashcard_performance=round(learner.flashcard_performance, 1),
        difficulty=learner.difficulty or "medium",
        last_reviewed=learner.last_reviewed.strftime("%Y-%m-%d %H:%M") if learner.last_reviewed else None,
        next_review=learner.next_review.strftime("%Y-%m-%d") if learner.next_review else None,
        recent_performance=learner.recent_performance_json or [],
        signals=signals_data["signals"],
        recommended_action=signals_data["recommended_action"],
        ai_insight=signals_data["ai_insight"]
    )

# =========================================================================
# 3. STUDY SESSIONS
# =========================================================================

@router.post("/study-sessions", response_model=StudySessionOut, status_code=status.HTTP_201_CREATED)
def create_study_session(
    payload: StudySessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record a study session. Updates progress study time and topic review records.
    """
    now = datetime.utcnow()
    session = StudySession(
        user_id=current_user.id,
        material_id=payload.material_id,
        duration_minutes=payload.duration_minutes,
        session_type=payload.session_type,
        topic=payload.topic,
        start_time=now,
        end_time=now
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    learner_service.update_after_study_session(
        db=db,
        user_id=current_user.id,
        duration_minutes=payload.duration_minutes,
        topic_name=payload.topic,
        session_type=payload.session_type
    )

    return StudySessionOut(
        id=session.id,
        duration_minutes=session.duration_minutes,
        session_type=session.session_type,
        material_id=session.material_id,
        topic=session.topic,
        start_time=session.start_time.strftime("%Y-%m-%d %H:%M")
    )

@router.get("/study-sessions", response_model=List[StudySessionOut])
def list_study_sessions(
    limit: int = 15,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List historical study sessions for the authenticated student.
    """
    sessions = (
        db.query(StudySession)
        .filter(StudySession.user_id == current_user.id)
        .order_by(StudySession.start_time.desc())
        .limit(limit)
        .all()
    )

    return [
        StudySessionOut(
            id=s.id,
            duration_minutes=s.duration_minutes,
            session_type=s.session_type,
            material_id=s.material_id,
            topic=s.topic,
            start_time=s.start_time.strftime("%Y-%m-%d %H:%M") if s.start_time else "Recent"
        )
        for s in sessions
    ]

# =========================================================================
# 4. GOALS MANAGEMENT
# =========================================================================

@router.get("/goals", response_model=List[GoalOut])
def get_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all study goals for the authenticated student."""
    goals = (
        db.query(Goal)
        .filter(Goal.user_id == current_user.id)
        .order_by(Goal.created_at.desc())
        .all()
    )

    # If new student has no goals, provision sensible default starting goals
    if not goals:
        default_goals = [
            Goal(user_id=current_user.id, title="Complete 5 topics", type="weekly", target=5, current=1, unit="topics"),
            Goal(user_id=current_user.id, title="Study 60 minutes", type="daily", target=60, current=35, unit="minutes"),
            Goal(user_id=current_user.id, title="Score 80%+ on 2 quizzes", type="weekly", target=2, current=1, unit="quizzes")
        ]
        db.add_all(default_goals)
        db.commit()
        goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()

    return [
        GoalOut(
            id=g.id,
            title=g.title,
            type=g.type,
            target=g.target,
            current=g.current,
            unit=g.unit,
            completed=g.completed,
            created_at=g.created_at.strftime("%Y-%m-%d") if g.created_at else "Today"
        )
        for g in goals
    ]

@router.post("/goals", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new study goal."""
    goal = Goal(
        user_id=current_user.id,
        title=payload.title,
        type=payload.type,
        target=payload.target,
        current=0,
        unit=payload.unit,
        completed=False,
        created_at=datetime.utcnow()
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    return GoalOut(
        id=goal.id,
        title=goal.title,
        type=goal.type,
        target=goal.target,
        current=goal.current,
        unit=goal.unit,
        completed=goal.completed,
        created_at=goal.created_at.strftime("%Y-%m-%d")
    )

@router.put("/goals/{id}", response_model=GoalOut)
def update_goal(
    id: int,
    payload: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update progress or completion status of a goal."""
    goal = db.query(Goal).filter(Goal.id == id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")

    if payload.title is not None:
        goal.title = payload.title
    if payload.target is not None:
        goal.target = payload.target
    if payload.current is not None:
        goal.current = payload.current
    if payload.completed is not None:
        goal.completed = payload.completed
        if goal.completed:
            goal.current = goal.target

    db.commit()
    db.refresh(goal)

    return GoalOut(
        id=goal.id,
        title=goal.title,
        type=goal.type,
        target=goal.target,
        current=goal.current,
        unit=goal.unit,
        completed=goal.completed,
        created_at=goal.created_at.strftime("%Y-%m-%d") if goal.created_at else "Today"
    )

@router.delete("/goals/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a study goal."""
    goal = db.query(Goal).filter(Goal.id == id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")
    db.delete(goal)
    db.commit()
    return None
