import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.viva import (
    VivaStartRequest,
    VivaStartResponse,
    VivaAnswerRequest,
    VivaAnswerResponse,
    VivaSessionDetailResponse,
    VivaHistoryResponse,
)
from app.services.viva_service import viva_service

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/viva", tags=["viva"])


@router.post("/start", response_model=VivaStartResponse, status_code=status.HTTP_201_CREATED)
def start_viva_session(
    payload: VivaStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Starts an interactive AI Viva / Technical Interview session.
    Generates Question 1 grounded in course study materials.
    """
    try:
        session_data = viva_service.start_session(
            db=db,
            user_id=current_user.id,
            topic=payload.topic,
            mode=payload.mode,
            difficulty=payload.difficulty,
            material_id=payload.material_id,
            total_questions=payload.total_questions
        )
        return session_data
    except Exception as e:
        logger.error(f"Error starting viva session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start viva session: {str(e)}"
        )


@router.post("/{session_id}/answer", response_model=VivaAnswerResponse)
def submit_viva_answer(
    session_id: int,
    payload: VivaAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits student's verbal/written answer for evaluation across 4 dimensions:
    Correctness, Relevance, Completeness, and Conceptual Understanding.
    Dynamically triggers adaptive follow-up or generates the next question.
    """
    try:
        result = viva_service.submit_answer(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            question_id=payload.question_id,
            answer_text=payload.answer_text
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"Error submitting viva answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate viva answer: {str(e)}"
        )


@router.post("/{session_id}/end", response_model=VivaSessionDetailResponse)
def end_viva_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Finalizes the viva session, aggregates dimensional scores, generates the final
    pedagogical report (strengths, weak areas, improvements), and updates the learner model.
    """
    try:
        session_report = viva_service.end_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        return session_report
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"Error ending viva session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finalize viva session: {str(e)}"
        )


@router.get("/history", response_model=VivaHistoryResponse)
def get_viva_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the authenticated student's past viva and interview sessions.
    """
    return viva_service.get_user_history(db=db, user_id=current_user.id)


@router.get("/{session_id}", response_model=VivaSessionDetailResponse)
def get_viva_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves full viva session transcript, question-by-question evaluations, and final summary report.
    """
    try:
        return viva_service.get_session_detail(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"Error fetching viva session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch viva session: {str(e)}"
        )
