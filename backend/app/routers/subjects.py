from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.subject import Subject, Topic
from app.schemas.subject import SubjectOut, TopicOut

router = APIRouter(prefix="/subjects", tags=["Subjects"])

@router.get("", response_model=List[SubjectOut])
def get_subjects(db: Session = Depends(get_db)):
    subjects = db.query(Subject).all()
    results = []
    for s in subjects:
        results.append(
            SubjectOut(
                id=s.id,
                name=s.name,
                code=s.code,
                description=s.description,
                topics_count=len(s.topics),
                topics=[
                    TopicOut(
                        id=t.id,
                        subject_id=t.subject_id,
                        name=t.name,
                        description=t.description,
                        order_index=t.order_index,
                        difficulty_level=t.difficulty_level
                    )
                    for t in s.topics
                ]
            )
        )
    return results

@router.get("/{subject_id}/topics", response_model=List[TopicOut])
def get_subject_topics(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with id {subject_id} was not found.",
        )
    return [
        TopicOut(
            id=t.id,
            subject_id=t.subject_id,
            name=t.name,
            description=t.description,
            order_index=t.order_index,
            difficulty_level=t.difficulty_level
        )
        for t in subject.topics
    ]
