import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.material import Material
from app.models.document import DocumentChunk
from app.models.study import Flashcard, Analytics
from app.models.learner import LearnerModel
from app.schemas.flashcard import (
    FlashcardGenerateRequest,
    FlashcardOut,
    FlashcardReviewRequest,
    FlashcardReviewResponse
)
from app.services.deps import get_current_user
from app.services.ai_service import ai_service

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/flashcards", tags=["Flashcards"])

def _format_flashcard(card: Flashcard) -> FlashcardOut:
    return FlashcardOut(
        id=card.id,
        material_id=card.material_id,
        topic=card.topic_name or (card.topic.name if card.topic else "General"),
        topic_name=card.topic_name or (card.topic.name if card.topic else "General"),
        front=card.front,
        back=card.back,
        difficulty=card.difficulty,
        source=card.source,
        created_at=card.created_at
    )

@router.post("/generate", response_model=List[FlashcardOut], status_code=status.HTTP_201_CREATED)
def generate_flashcards(
    payload: FlashcardGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate structured active recall flashcards from study material using Gemini.
    Stores and associates generated flashcards with the user and material.
    """
    material_id = payload.get_material_id()
    if not material_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="material_id is required for flashcard generation."
        )

    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study material '{material_id}' not found."
        )

    # Gather content from DocumentChunks or material content
    chunks = db.query(DocumentChunk).filter(DocumentChunk.material_id == material.id).order_by(DocumentChunk.chunk_index).all()
    if chunks:
        if payload.topic and payload.topic != "All topics":
            # Prefer chunks mentioning topic
            topic_lower = payload.topic.lower()
            matching = [c.content for c in chunks if topic_lower in c.content.lower()]
            content_text = "\n\n".join(matching) if matching else "\n\n".join([c.content for c in chunks[:4]])
        else:
            content_text = "\n\n".join([c.content for c in chunks[:5]])
    else:
        content_text = material.content_text or material.description or material.title

    count = max(1, min(payload.count or 5, 20))
    difficulty = payload.difficulty or "medium"

    # AI generation
    raw_cards = ai_service.generate_flashcards_from_material(
        material_title=material.title,
        content_text=content_text,
        topic=payload.topic,
        count=count,
        difficulty=difficulty
    )

    created_records = []
    for item in raw_cards:
        card = Flashcard(
            user_id=current_user.id,
            material_id=material.id,
            topic_name=item.get("topic") or payload.topic or material.title,
            front=item["front"],
            back=item["back"],
            difficulty=item.get("difficulty") or difficulty,
            source=item.get("source") or material.title,
            created_at=datetime.utcnow()
        )
        db.add(card)
        created_records.append(card)

    db.commit()
    for card in created_records:
        db.refresh(card)

    logger.info(f"Generated {len(created_records)} flashcards for material '{material.id}'.")
    return [_format_flashcard(c) for c in created_records]

@router.get("", response_model=List[FlashcardOut])
def list_flashcards(
    material_id: Optional[str] = Query(None, alias="materialId"),
    topic: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve flashcards for a specific material or all flashcards accessible to the user.
    """
    query = db.query(Flashcard)
    if material_id:
        query = query.filter(Flashcard.material_id == material_id)
    if topic and topic != "All topics":
        query = query.filter(Flashcard.topic_name.ilike(f"%{topic}%"))

    # Return user's cards plus system/shared cards
    cards = query.order_by(Flashcard.id.asc()).all()

    # If requested by material and none exist yet, auto-generate initial deck so the user immediately has cards
    if not cards and material_id:
        mat = db.query(Material).filter(Material.id == material_id).first()
        if mat:
            chunks = db.query(DocumentChunk).filter(DocumentChunk.material_id == mat.id).order_by(DocumentChunk.chunk_index).all()
            content_text = "\n\n".join([c.content for c in chunks[:5]]) if chunks else (mat.description or mat.title)
            generated = ai_service.generate_flashcards_from_material(
                material_title=mat.title,
                content_text=content_text,
                topic=topic,
                count=5,
                difficulty="medium"
            )
            for item in generated:
                new_card = Flashcard(
                    user_id=current_user.id,
                    material_id=mat.id,
                    topic_name=item.get("topic") or mat.title,
                    front=item["front"],
                    back=item["back"],
                    difficulty=item.get("difficulty", "medium"),
                    source=item.get("source") or mat.title
                )
                db.add(new_card)
                cards.append(new_card)
            db.commit()
            for c in cards:
                db.refresh(c)

    return [_format_flashcard(c) for c in cards]

@router.get("/{id}", response_model=FlashcardOut)
def get_flashcard(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a single flashcard by ID."""
    card = db.query(Flashcard).filter(Flashcard.id == id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flashcard with ID {id} not found."
        )
    return _format_flashcard(card)

@router.post("/{id}/review", response_model=FlashcardReviewResponse)
def review_flashcard(
    id: int,
    payload: FlashcardReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record student practice rating for a flashcard (easy/medium/hard).
    Updates topic mastery and flashcard performance in the LearnerModel.
    """
    card = db.query(Flashcard).filter(Flashcard.id == id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flashcard with ID {id} not found."
        )

    rating_str = payload.rating.lower().strip()
    from app.services.learner_service import learner_service
    topic_name = learner_service.normalize_topic_name(card.topic_name or "General", db=db)

    learner = learner_service.update_topic_after_flashcard(
        db=db,
        user_id=current_user.id,
        topic_name=topic_name,
        rating=rating_str
    )

    # Track analytics event
    event = Analytics(
        user_id=current_user.id,
        event_type="flashcard_review",
        event_data_json={
            "card_id": card.id,
            "topic": topic_name,
            "rating": rating_str,
            "material_id": card.material_id
        },
        timestamp=datetime.utcnow()
    )
    db.add(event)
    db.commit()
    db.refresh(learner)

    return FlashcardReviewResponse(
        success=True,
        card_id=card.id,
        topic=topic_name,
        rating=rating_str,
        flashcard_performance=learner.flashcard_performance,
        message=f"Recorded review as '{rating_str}'. Learner model updated."
    )
