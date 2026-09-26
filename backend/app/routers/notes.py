import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User
from app.models.study import Note
from app.models.material import Material
from app.schemas.note import (
    NoteCreate,
    NoteUpdate,
    NoteOut,
    AIGenerateNotesRequest,
    AIGenerateNotesResponse,
)
from app.services.deps import get_current_user
from app.services.ai_service import ai_service

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/notes", tags=["Notes & PDF Export"])

def _format_note(note: Note) -> NoteOut:
    mat_title = note.material.title if note.material else None
    return NoteOut(
        id=note.id,
        user_id=note.user_id,
        material_id=note.material_id,
        material_title=mat_title,
        title=note.title,
        topic=note.topic or "General",
        content=note.content,
        key_points=note.key_points_json or [],
        examples=note.examples_json or [],
        tags=note.tags_json or [],
        is_favorite=note.is_favorite or False,
        created_at=note.created_at.strftime("%Y-%m-%d %H:%M") if note.created_at else "Recently",
        updated_at=note.updated_at.strftime("%Y-%m-%d %H:%M") if note.updated_at else "Recently",
    )

@router.get("", response_model=List[NoteOut])
def list_notes(
    topic: Optional[str] = None,
    search: Optional[str] = None,
    favorites_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all notes created by the current student."""
    query = db.query(Note).filter(Note.user_id == current_user.id)

    if topic and topic.lower() != "all":
        query = query.filter(Note.topic.ilike(f"%{topic}%"))
    if favorites_only:
        query = query.filter(Note.is_favorite == True)
    if search:
        s = f"%{search}%"
        query = query.filter((Note.title.ilike(s)) | (Note.content.ilike(s)) | (Note.topic.ilike(s)))

    notes = query.order_by(desc(Note.is_favorite), desc(Note.updated_at)).all()
    return [_format_note(n) for n in notes]

@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new study note with key takeaways and examples."""
    note = Note(
        user_id=current_user.id,
        material_id=payload.material_id,
        title=payload.title.strip(),
        topic=payload.topic or "General",
        content=payload.content.strip(),
        key_points_json=payload.key_points or [],
        examples_json=payload.examples or [],
        tags_json=payload.tags or [],
        is_favorite=payload.is_favorite or False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return _format_note(note)

@router.post("/generate", response_model=AIGenerateNotesResponse)
def generate_note_from_ai(
    payload: AIGenerateNotesRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Uses AI to analyze an explanation or topic and generate structured academic notes,
    complete with headers, core takeaways, and illustrative examples.
    """
    result = ai_service.generate_structured_notes(
        content_or_prompt=payload.content_or_prompt,
        topic=payload.topic,
    )
    return AIGenerateNotesResponse(**result)

@router.get("/{id}", response_model=NoteOut)
def get_note(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve an individual note."""
    note = db.query(Note).filter(Note.id == id, Note.user_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    return _format_note(note)

@router.put("/{id}", response_model=NoteOut)
def update_note(
    id: int,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing note."""
    note = db.query(Note).filter(Note.id == id, Note.user_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")

    if payload.title is not None:
        note.title = payload.title.strip()
    if payload.topic is not None:
        note.topic = payload.topic.strip()
    if payload.content is not None:
        note.content = payload.content.strip()
    if payload.key_points is not None:
        note.key_points_json = payload.key_points
    if payload.examples is not None:
        note.examples_json = payload.examples
    if payload.tags is not None:
        note.tags_json = payload.tags
    if payload.is_favorite is not None:
        note.is_favorite = payload.is_favorite

    note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    return _format_note(note)

@router.delete("/{id}")
def delete_note(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a note."""
    note = db.query(Note).filter(Note.id == id, Note.user_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    db.delete(note)
    db.commit()
    return {"message": "Note deleted successfully."}
