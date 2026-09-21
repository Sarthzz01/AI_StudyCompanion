import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.document import Summary
from app.models.material import Material
from app.schemas.summary import SummaryOut, SummarySection, SummaryGenerateRequest
from app.services.deps import get_current_user
from app.services.rag_service import rag_service

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/summaries", tags=["Summaries"])

def _format_summary(summary_rec: Summary, material_title: Optional[str] = None) -> SummaryOut:
    raw_sections = summary_rec.sections_json or []
    sections = [
        SummarySection(
            id=s.get("id", f"s{idx+1}"),
            title=s.get("title", f"Section {idx+1}"),
            body=s.get("body", ""),
            points=s.get("points", [])
        )
        for idx, s in enumerate(raw_sections)
    ]
    return SummaryOut(
        id=str(summary_rec.id),
        materialId=summary_rec.material_id,
        materialTitle=material_title,
        generatedAt=summary_rec.generated_at_str or "Recently",
        keyConcepts=summary_rec.key_concepts_json or [],
        sections=sections
    )

@router.get("", response_model=List[SummaryOut])
def list_summaries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all generated study summaries."""
    summaries = db.query(Summary).order_by(Summary.created_at.desc()).all()
    out = []
    for s in summaries:
        mat = db.query(Material).filter(Material.id == s.material_id).first()
        out.append(_format_summary(s, mat.title if mat else None))
    return out

@router.get("/{material_id}", response_model=SummaryOut)
def get_summary(
    material_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if requested by material ID
    mat = db.query(Material).filter(Material.id == material_id).first()
    if not mat:
        # Check if material_id is actually a numeric summary ID
        try:
            summary_id_int = int(material_id)
            summary_by_id = db.query(Summary).filter(Summary.id == summary_id_int).first()
            if summary_by_id:
                mat = db.query(Material).filter(Material.id == summary_by_id.material_id).first()
                return _format_summary(summary_by_id, mat.title if mat else None)
        except ValueError:
            pass

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study material or summary '{material_id}' not found."
        )

    user_role = current_user.role.name.lower() if current_user.role else "student"
    if user_role not in ["instructor", "admin"] and mat.user_id != current_user.id:
        mat_creator_role = mat.user.role.name.lower() if mat.user and mat.user.role else "instructor"
        if mat_creator_role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access another student's private study material."
            )

    res = rag_service.generate_summary(
        db=db,
        user=current_user,
        material_id=material_id,
        force_refresh=False
    )

    sections = [
        SummarySection(
            id=s["id"],
            title=s["title"],
            body=s["body"],
            points=s.get("points", [])
        )
        for s in res.get("sections", [])
    ]

    return SummaryOut(
        id=res["id"],
        materialId=res["materialId"],
        materialTitle=res.get("materialTitle", mat.title),
        generatedAt=res["generatedAt"],
        keyConcepts=res.get("keyConcepts", []),
        sections=sections
    )

@router.post("/generate", response_model=SummaryOut)
def generate_summary_endpoint(
    payload: SummaryGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate or re-generate an in-depth structured study summary for a material."""
    mat_id = payload.get_material_id()
    if not mat_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="materialId is required."
        )

    mat = db.query(Material).filter(Material.id == mat_id).first()
    if not mat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study material '{mat_id}' not found."
        )

    user_role = current_user.role.name.lower() if current_user.role else "student"
    if user_role not in ["instructor", "admin"] and mat.user_id != current_user.id:
        mat_creator_role = mat.user.role.name.lower() if mat.user and mat.user.role else "instructor"
        if mat_creator_role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access another student's private study material."
            )

    res = rag_service.generate_summary(
        db=db,
        user=current_user,
        material_id=mat_id,
        force_refresh=True
    )

    sections = [
        SummarySection(
            id=s["id"],
            title=s["title"],
            body=s["body"],
            points=s.get("points", [])
        )
        for s in res.get("sections", [])
    ]

    return SummaryOut(
        id=res["id"],
        materialId=res["materialId"],
        materialTitle=res.get("materialTitle", mat.title),
        generatedAt=res["generatedAt"],
        keyConcepts=res.get("keyConcepts", []),
        sections=sections
    )
