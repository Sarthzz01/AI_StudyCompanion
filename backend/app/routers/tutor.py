import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.material import Material
from app.schemas.tutor import TutorAskRequest, TutorAskResponse, SourceReferenceOut
from app.services.deps import get_current_user
from app.services.rag_service import rag_service

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/tutor", tags=["AI Tutor"])

@router.post("/ask", response_model=TutorAskResponse)
def ask_tutor(
    payload: TutorAskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RAG-grounded AI Tutor endpoint.
    Answers strictly from the selected study material chunks and provides source/page citations.
    Guards against external hallucinations and verifies access permissions.
    """
    if not payload.question or not payload.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A question is required."
        )

    material_id = payload.get_material_id()
    if material_id:
        mat = db.query(Material).filter(Material.id == material_id).first()
        if not mat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Study material '{material_id}' not found or has been deleted."
            )
        
        user_role = current_user.role.name.lower() if current_user.role else "student"
        if user_role not in ["instructor", "admin"] and mat.user_id != current_user.id:
            mat_creator_role = mat.user.role.name.lower() if mat.user and mat.user.role else "instructor"
            if mat_creator_role == "student":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access another student's private study material."
                )

    try:
        result = rag_service.ask_grounded_tutor(
            db=db,
            user=current_user,
            question=payload.question.strip(),
            material_id=material_id
        )

        sources = [
            SourceReferenceOut(label=s["label"], page=s["page"])
            for s in result.get("sources", [])
        ]

        return TutorAskResponse(
            answer=result["answer"],
            sources=sources,
            grounded=result.get("grounded", True)
        )
    except Exception as e:
        logger.error(f"Error in ask_tutor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tutor failed to generate answer: {str(e)}"
        )
