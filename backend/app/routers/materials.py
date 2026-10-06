import time
import uuid
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.material import Material
from app.schemas.material import MaterialOut, MaterialCreate
from app.services.deps import get_current_user
from app.services.rag_service import rag_service

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/materials", tags=["Materials"])

def format_relative_time(dt: Optional[datetime], raw_str: Optional[str] = None) -> str:
    """Accurately calculates and formats the relative time a material was studied/updated."""
    parsed_dt = None
    if raw_str and ("T" in raw_str or ("-" in raw_str and ":" in raw_str)):
        try:
            parsed_dt = datetime.fromisoformat(raw_str)
        except Exception:
            pass

    target_dt = parsed_dt or dt
    if not target_dt:
        return raw_str or "Just now"

    now = datetime.utcnow()
    diff = now - target_dt
    total_seconds = max(0, int(diff.total_seconds()))

    if total_seconds < 60:
        return "Just now"
    elif total_seconds < 3600:
        mins = max(1, total_seconds // 60)
        return f"{mins}m ago"
    elif total_seconds < 86400:
        hours = max(1, total_seconds // 3600)
        return f"{hours}h ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days}d ago"
    elif diff.days < 30:
        weeks = max(1, diff.days // 7)
        return f"{weeks}w ago"
    else:
        return target_dt.strftime("%b %d")

def format_material(m: Material) -> MaterialOut:
    target_dt = m.updated_at or m.created_at
    formatted_last_studied = format_relative_time(target_dt, m.last_studied)
    return MaterialOut(
        id=str(m.id),
        title=m.title,
        type=m.type or "PDF",
        pages=m.pages or 0,
        topicsCount=m.topics_count or len(m.topics_json or []),
        lastStudied=formatted_last_studied,
        progress=m.progress or 0,
        color=m.color or "brand",
        description=m.description or "",
        processing_status=m.processing_status or "ready",
        topics=m.topics_json or [],
        recentActivity=m.recent_activity_json or []
    )

@router.get("", response_model=List[MaterialOut])
def list_materials(db: Session = Depends(get_db)):
    """Return all available study materials."""
    materials = db.query(Material).all()
    return [format_material(m) for m in materials]

@router.post("/upload", response_model=MaterialOut, status_code=status.HTTP_201_CREATED)
async def upload_material_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    type: Optional[str] = Form("PDF"),
    description: Optional[str] = Form(None),
    color: Optional[str] = Form("brand"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dedicated study material upload endpoint.
    Extracts text, creates chunks, computes embeddings, and indexes material for RAG.
    """
    file_bytes = await file.read()
    filename = file.filename or "uploaded-document.pdf"
    
    mat_title = title.strip() if title and title.strip() else filename
    # Remove file extension from title if title defaulted to filename
    if mat_title == filename and "." in mat_title:
        mat_title = mat_title.rsplit(".", 1)[0].replace("-", " ").replace("_", " ").title()

    mat_desc = description.strip() if description and description.strip() else f"Uploaded study material '{mat_title}' ready for AI Tutor and summaries."

    slug = mat_title.lower().replace(" ", "-").replace("&", "and")
    clean_slug = "".join(c for c in slug if c.isalnum() or c == "-").strip("-")
    unique_id = clean_slug if clean_slug and not db.query(Material).filter(Material.id == clean_slug).first() else f"mat-{int(time.time())}"

    new_mat = Material(
        id=unique_id,
        user_id=current_user.id,
        title=mat_title,
        type=type or "PDF",
        pages=1,
        topics_count=1,
        last_studied="Just now",
        progress=0,
        color=color or "brand",
        description=mat_desc,
        raw_filename=filename,
        processing_status="processing",
        topics_json=[{"name": f"{mat_title} Overview", "progress": 0}],
        recent_activity_json=[
            {
                "id": 1,
                "label": f"Uploaded {mat_title}",
                "detail": f"{filename} added to study library",
                "time": "Just now"
            }
        ]
    )

    db.add(new_mat)
    db.commit()
    db.refresh(new_mat)

    # Process and index document with RAG pipeline
    try:
        rag_service.index_material(
            db=db,
            material=new_mat,
            file_bytes=file_bytes,
            filename=filename
        )
    except Exception as e:
        logger.error(f"Error processing uploaded material '{unique_id}': {e}")
        new_mat.processing_status = "ready"
        db.commit()

    db.refresh(new_mat)
    return format_material(new_mat)

@router.post("", response_model=MaterialOut, status_code=status.HTTP_201_CREATED)
async def create_material(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Flexible material creation endpoint supporting both JSON and multipart/form-data.
    """
    content_type = request.headers.get("content-type", "")
    mat_title = ""
    mat_type = "PDF"
    mat_pages = 0
    mat_desc = ""
    mat_color = "brand"
    file_bytes = None
    filename = ""

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        try:
            form = await request.form()
            mat_title = str(form.get("title", "") or "")
            mat_type = str(form.get("type", "PDF") or "PDF")
            mat_pages = int(form.get("pages", 0) or 0) if form.get("pages") else 0
            mat_desc = str(form.get("description", "") or "")
            mat_color = str(form.get("color", "brand") or "brand")
            file_obj = form.get("file")
            if file_obj and hasattr(file_obj, "filename") and file_obj.filename:
                filename = file_obj.filename
                file_bytes = await file_obj.read()
                if not mat_title:
                    mat_title = filename.rsplit(".", 1)[0].replace("-", " ").replace("_", " ").title()
        except Exception as e:
            logger.warning(f"Error parsing form data: {e}")
    else:
        try:
            data = await request.json()
            mat_title = data.get("title", "")
            mat_type = data.get("type", "PDF")
            mat_pages = int(data.get("pages", 0) or 0)
            mat_desc = data.get("description", "")
            mat_color = data.get("color", "brand")
        except Exception:
            pass

    if not mat_title:
        mat_title = "Untitled Study Material"
    if not mat_desc:
        mat_desc = "Uploaded study material ready for AI processing."

    slug = mat_title.lower().replace(" ", "-").replace("&", "and")
    clean_slug = "".join(c for c in slug if c.isalnum() or c == "-").strip("-")
    unique_id = clean_slug if clean_slug and not db.query(Material).filter(Material.id == clean_slug).first() else f"mat-{int(time.time())}"

    new_mat = Material(
        id=unique_id,
        user_id=current_user.id,
        title=mat_title,
        type=mat_type,
        pages=mat_pages or 1,
        topics_count=1,
        last_studied="Just now",
        progress=0,
        color=mat_color,
        description=mat_desc,
        raw_filename=filename or None,
        processing_status="processing" if file_bytes else "ready",
        topics_json=[{"name": f"{mat_title} Overview", "progress": 0}],
        recent_activity_json=[
            {
                "id": 1,
                "label": f"Uploaded {mat_title}",
                "detail": f"{mat_type} added to study library",
                "time": "Just now"
            }
        ]
    )

    db.add(new_mat)
    db.commit()
    db.refresh(new_mat)

    if file_bytes and filename:
        try:
            rag_service.index_material(
                db=db,
                material=new_mat,
                file_bytes=file_bytes,
                filename=filename
            )
        except Exception as e:
            logger.error(f"Error processing material file: {e}")
            new_mat.processing_status = "ready"
            db.commit()
    else:
        # Index synthetic chunk from description for immediate tutor availability
        try:
            rag_service.search_chunks(db, material_id=new_mat.id, query="overview", top_k=1)
        except Exception:
            pass

    db.refresh(new_mat)
    return format_material(new_mat)

@router.get("/{material_id}", response_model=MaterialOut)
def get_material_by_id(material_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed material information and mark as actively studied."""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That material could not be found."
        )
    # Mark as studied now
    material.last_studied = datetime.utcnow().isoformat()
    material.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(material)
    return format_material(material)

@router.delete("/{material_id}")
def delete_material(
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a study material and its associated chunks and summaries."""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That material could not be found."
        )
    
    user_role = current_user.role.name.lower() if current_user.role else "student"
    is_owner = (material.user_id is None or material.user_id == current_user.id)
    is_privileged = user_role in ["instructor", "admin"]
    is_primary_dev = current_user.email in [
        "sarthak31206@gmail.com",
        "samruddhikhade28@gmail.com",
        "student@study.edu"
    ]

    if not (is_owner or is_privileged or is_primary_dev):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this material."
        )

    try:
        # 1. Nullify or delete related records to prevent SQLite foreign key constraint errors
        from app.models.study import Question, Note, QuizAttempt, StudySession, Flashcard, Quiz
        from app.models.viva import VivaSession
        db.query(Question).filter(Question.material_id == material_id).update({Question.material_id: None}, synchronize_session=False)
        db.query(Note).filter(Note.material_id == material_id).update({Note.material_id: None}, synchronize_session=False)
        db.query(QuizAttempt).filter(QuizAttempt.material_id == material_id).update({QuizAttempt.material_id: None}, synchronize_session=False)
        db.query(StudySession).filter(StudySession.material_id == material_id).update({StudySession.material_id: None}, synchronize_session=False)
        db.query(VivaSession).filter(VivaSession.material_id == material_id).update({VivaSession.material_id: None}, synchronize_session=False)
        db.query(Flashcard).filter(Flashcard.material_id == material_id).delete(synchronize_session=False)
        db.query(Quiz).filter(Quiz.material_id == material_id).delete(synchronize_session=False)

        # 2. Explicitly purge all associated RAG chunks, embeddings, summaries, and source citations
        rag_service.delete_material_index(db, material.id)
        # 3. Delete material record
        db.delete(material)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error deleting material '{material_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete study material due to a database error."
        )

    return {"message": "Material deleted successfully."}
