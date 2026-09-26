import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models.user import User
from app.models.material import Material
from app.models.document import TutorInteraction
from app.schemas.tutor import (
    TutorAskRequest,
    TutorAskResponse,
    SourceReferenceOut,
    TutorHistoryItemOut,
    TutorConversationSummary
)
from app.services.deps import get_current_user
from app.services.openai_service import openai_service
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
    Unified AI Tutor endpoint powered by OpenAI LLM (Responses API).
    Capable of answering general academic and conversational questions.
    """
    query = payload.get_query()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A question or message is required."
        )

    material_id = payload.get_material_id()
    conversation_id = payload.get_conversation_id()
    
    # Generate new conversation ID if starting a new chat
    if not conversation_id or conversation_id.strip() == "":
        conversation_id = f"conv_{uuid.uuid4().hex[:12]}"

    # Determine or reuse conversation title
    existing_conv_first = (
        db.query(TutorInteraction)
        .filter(
            TutorInteraction.user_id == current_user.id,
            TutorInteraction.conversation_id == conversation_id
        )
        .order_by(TutorInteraction.created_at.asc())
        .first()
    )
    
    if existing_conv_first and existing_conv_first.title:
        conv_title = existing_conv_first.title
    else:
        # Create a clean title from the user query
        conv_title = query[:45].strip()
        if len(query) > 45:
            conv_title += "…"

    context_blocks: List[str] = []
    sources: List[SourceReferenceOut] = []
    is_material_grounded = False

    # 1. Check if user targeted a specific study material
    if material_id and material_id not in ["general", "all", "none"]:
        mat = db.query(Material).filter(Material.id == material_id).first()
        if mat:
            user_role = current_user.role.name.lower() if current_user.role else "student"
            if user_role not in ["instructor", "admin"] and mat.user_id != current_user.id:
                mat_creator_role = mat.user.role.name.lower() if mat.user and mat.user.role else "instructor"
                if mat_creator_role == "student":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You do not have permission to access another student's private study material."
                    )
            
            try:
                relevant_chunks = rag_service.search_chunks(db, material_id=material_id, query=query, top_k=3)
                seen_pages = set()
                for chunk, score in relevant_chunks:
                    page_label = f"Page {chunk.page_number}"
                    context_blocks.append(f"[Excerpt from {mat.title}, {page_label}]:\n{chunk.content}")
                    if chunk.page_number not in seen_pages:
                        sources.append(SourceReferenceOut(
                            label=mat.title,
                            page=page_label
                        ))
                        seen_pages.add(chunk.page_number)
                if sources:
                    is_material_grounded = True
            except Exception as search_err:
                logger.warning(f"Material chunk search skipped: {search_err}")

    # 2. Prepare conversation history for contextual follow-up questions
    history = []
    if payload.history and isinstance(payload.history, list):
        history = payload.history
    else:
        try:
            # Load messages for this specific conversation
            prev_interactions = (
                db.query(TutorInteraction)
                .filter(
                    TutorInteraction.user_id == current_user.id,
                    TutorInteraction.conversation_id == conversation_id
                )
                .order_by(TutorInteraction.created_at.desc())
                .limit(8)
                .all()
            )
            for pi in reversed(prev_interactions):
                history.append({"role": "user", "content": pi.question})
                history.append({"role": "assistant", "content": pi.answer})
        except Exception as hist_err:
            logger.warning(f"Could not load conversation history from db: {hist_err}")

    # 3. Generate answer via OpenAI Service (Responses API)
    try:
        tutor_result = openai_service.generate_tutor_response(
            message=query,
            history=history,
            context_excerpts=context_blocks if context_blocks else None
        )
        answer = tutor_result.get("answer", "")
        model_used = tutor_result.get("model")
    except Exception as e:
        logger.error(f"Error in ask_tutor generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The AI Tutor is temporarily unable to generate a response. Please try again."
        )

    # 4. Save interaction to database for conversation history persistence
    try:
        valid_mat_id = material_id if (material_id and material_id not in ["general", "all", "none"]) else "general"
        interaction = TutorInteraction(
            user_id=current_user.id,
            material_id=valid_mat_id,
            conversation_id=conversation_id,
            title=conv_title,
            question=query,
            answer=answer,
            grounded=is_material_grounded,
            sources_json=[{"label": s.label, "page": s.page} for s in sources]
        )
        db.add(interaction)
        db.commit()
    except Exception as db_err:
        logger.warning(f"Could not persist tutor interaction: {db_err}")
        db.rollback()

    return TutorAskResponse(
        answer=answer,
        sources=sources,
        grounded=is_material_grounded,
        model=model_used,
        conversation_id=conversation_id,
        title=conv_title
    )

@router.get("/conversations", response_model=List[TutorConversationSummary])
def get_tutor_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the student's list of conversation sessions (like ChatGPT sidebar history).
    """
    try:
        # Group by conversation_id to get summary
        records = (
            db.query(
                TutorInteraction.conversation_id,
                func.max(TutorInteraction.title).label("title"),
                func.max(TutorInteraction.created_at).label("last_activity"),
                func.min(TutorInteraction.created_at).label("first_activity"),
                func.count(TutorInteraction.id).label("message_count")
            )
            .filter(TutorInteraction.user_id == current_user.id)
            .group_by(TutorInteraction.conversation_id)
            .order_by(desc("last_activity"))
            .all()
        )

        results = []
        for r in records:
            conv_id = r.conversation_id
            if not conv_id:
                # If an old record has no conversation_id, skip or assign generic
                continue
            
            # Fetch the latest question/answer snippet for display
            latest_interaction = (
                db.query(TutorInteraction)
                .filter(
                    TutorInteraction.user_id == current_user.id,
                    TutorInteraction.conversation_id == conv_id
                )
                .order_by(TutorInteraction.created_at.desc())
                .first()
            )

            title = r.title or (latest_interaction.question[:45] if latest_interaction else "New Conversation")
            last_msg = latest_interaction.question if latest_interaction else ""

            results.append(TutorConversationSummary(
                conversation_id=conv_id,
                title=title,
                last_message=last_msg,
                updated_at=r.last_activity.strftime("%Y-%m-%d %H:%M") if r.last_activity else "",
                created_at=r.first_activity.strftime("%Y-%m-%d %H:%M") if r.first_activity else "",
                message_count=r.message_count,
                material_id=latest_interaction.material_id if latest_interaction else None
            ))

        return results
    except Exception as e:
        logger.error(f"Error fetching tutor conversations: {e}")
        return []

@router.get("/conversations/{conversation_id}", response_model=List[TutorHistoryItemOut])
def get_tutor_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves all messages for a specific conversation thread in chronological order.
    """
    try:
        records = (
            db.query(TutorInteraction)
            .filter(
                TutorInteraction.user_id == current_user.id,
                TutorInteraction.conversation_id == conversation_id
            )
            .order_by(TutorInteraction.created_at.asc())
            .all()
        )

        return [
            TutorHistoryItemOut(
                id=r.id,
                question=r.question,
                answer=r.answer,
                grounded=r.grounded,
                material_id=r.material_id,
                conversation_id=r.conversation_id,
                created_at=r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
                sources=[
                    SourceReferenceOut(label=s.get("label", ""), page=s.get("page", ""))
                    for s in (r.sources_json or [])
                ]
            )
            for r in records
        ]
    except Exception as e:
        logger.error(f"Error fetching conversation messages: {e}")
        raise HTTPException(status_code=500, detail="Could not load conversation.")

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tutor_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes an entire conversation thread.
    """
    try:
        db.query(TutorInteraction).filter(
            TutorInteraction.user_id == current_user.id,
            TutorInteraction.conversation_id == conversation_id
        ).delete()
        db.commit()
    except Exception as e:
        logger.error(f"Error deleting tutor conversation: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation."
        )

@router.get("/history", response_model=List[TutorHistoryItemOut])
def get_tutor_history(
    material_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Backward-compatible history endpoint.
    """
    try:
        query = db.query(TutorInteraction).filter(TutorInteraction.user_id == current_user.id)
        if material_id and material_id not in ["all", "general"]:
            query = query.filter(TutorInteraction.material_id == material_id)
        
        records = query.order_by(TutorInteraction.created_at.desc()).limit(limit).all()
        return [
            TutorHistoryItemOut(
                id=r.id,
                question=r.question,
                answer=r.answer,
                grounded=r.grounded,
                material_id=r.material_id,
                conversation_id=r.conversation_id,
                created_at=r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
                sources=[
                    SourceReferenceOut(label=s.get("label", ""), page=s.get("page", ""))
                    for s in (r.sources_json or [])
                ]
            )
            for r in reversed(records)
        ]
    except Exception as e:
        logger.error(f"Error fetching tutor history: {e}")
        return []

@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_tutor_history(
    material_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clears all conversation history for the student.
    """
    try:
        query = db.query(TutorInteraction).filter(TutorInteraction.user_id == current_user.id)
        if material_id and material_id not in ["all", "general"]:
            query = query.filter(TutorInteraction.material_id == material_id)
        query.delete()
        db.commit()
    except Exception as e:
        logger.error(f"Error clearing tutor history: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear history."
        )
