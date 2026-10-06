import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.study import Notification, Goal
from app.models.learner import LearnerModel
from app.schemas.notification import NotificationOut, NotificationsListOut, NotificationCreate
from app.services.deps import get_current_user

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/notifications", tags=["Notifications"])

def format_relative_time(dt: datetime) -> str:
    """Format datetime into a user-friendly relative timestamp."""
    if not dt:
        return "Recent"
    now = datetime.utcnow()
    diff = now - dt
    if diff.total_seconds() < 60:
        return "Just now"
    elif diff.total_seconds() < 3600:
        mins = int(diff.total_seconds() // 60)
        return f"{mins}m ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() // 3600)
        return f"{hours}h ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days}d ago"
    else:
        return dt.strftime("%b %d")

def ensure_dynamic_notifications(db: Session, user_id: int):
    """
    Checks student telemetry and generates timely notifications for:
    - Due spaced repetition reviews
    - Welcome / onboarding guidance
    """
    now = datetime.utcnow()
    existing_count = db.query(Notification).filter(Notification.user_id == user_id).count()

    if existing_count == 0:
        # Initial welcome notification for new student
        welcome = Notification(
            user_id=user_id,
            title="Welcome to AI Study Companion",
            message="Your AI-powered adaptive study companion is ready. Upload materials, take quizzes, or start an AI Viva session!",
            type="info",
            is_read=False,
            created_at=now
        )
        db.add(welcome)
        db.commit()

    # Check for overdue spaced repetition topics (due on or before now)
    due_topics = (
        db.query(LearnerModel)
        .filter(
            LearnerModel.user_id == user_id,
            LearnerModel.next_review != None,
            LearnerModel.next_review <= now
        )
        .all()
    )

    if due_topics:
        # Check if we already sent a revision reminder today
        start_of_today = datetime(now.year, now.month, now.day)
        recent_rev_notif = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.type == "revision",
                Notification.created_at >= start_of_today
            )
            .first()
        )
        if not recent_rev_notif:
            top_topic = due_topics[0].topic
            total_due = len(due_topics)
            msg = f"{top_topic} is due for spaced revision today." if total_due == 1 else f"{total_due} topics are due for spaced revision today, including {top_topic}."
            notif = Notification(
                user_id=user_id,
                title="Spaced Revision Due",
                message=msg,
                type="revision",
                is_read=False,
                created_at=now
            )
            db.add(notif)
            db.commit()

@router.get("", response_model=List[NotificationOut])
def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve real notifications for the authenticated student.
    Ensures active reminders (spaced repetition, system events) are populated.
    """
    ensure_dynamic_notifications(db, current_user.id)

    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit).all()

    return [
        NotificationOut(
            id=n.id,
            title=n.title,
            body=n.message,
            message=n.message,
            type=n.type,
            read=n.is_read,
            time=format_relative_time(n.created_at),
            created_at=n.created_at
        )
        for n in notifications
    ]

@router.get("/summary", response_model=NotificationsListOut)
def get_notifications_summary(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notifications along with unread and total count metadata.
    """
    ensure_dynamic_notifications(db, current_user.id)

    total_count = db.query(Notification).filter(Notification.user_id == current_user.id).count()
    unread_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(limit)
        .all()
    )

    items = [
        NotificationOut(
            id=n.id,
            title=n.title,
            body=n.message,
            type=n.type,
            read=n.is_read,
            time=format_relative_time(n.created_at),
            created_at=n.created_at
        )
        for n in notifications
    ]

    return NotificationsListOut(
        notifications=items,
        unread_count=unread_count,
        total_count=total_count
    )

@router.post("", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a student notification.
    """
    notif = Notification(
        user_id=current_user.id,
        title=payload.title,
        message=payload.message,
        type=payload.type,
        is_read=False,
        created_at=datetime.utcnow()
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    return NotificationOut(
        id=notif.id,
        title=notif.title,
        body=notif.message,
        type=notif.type,
        read=notif.is_read,
        time=format_relative_time(notif.created_at),
        created_at=notif.created_at
    )

@router.put("/{id}/read", response_model=NotificationOut)
def mark_notification_read(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a specific notification as read.
    """
    notif = db.query(Notification).filter(
        Notification.id == id,
        Notification.user_id == current_user.id
    ).first()

    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    notif.is_read = True
    db.commit()
    db.refresh(notif)

    return NotificationOut(
        id=notif.id,
        title=notif.title,
        body=notif.message,
        type=notif.type,
        read=notif.is_read,
        time=format_relative_time(notif.created_at),
        created_at=notif.created_at
    )

@router.put("/read-all", status_code=status.HTTP_200_OK)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark all notifications as read for the authenticated student.
    """
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()

    return {"message": "All notifications marked as read."}

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific notification.
    """
    notif = db.query(Notification).filter(
        Notification.id == id,
        Notification.user_id == current_user.id
    ).first()

    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    db.delete(notif)
    db.commit()
    return None

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_all_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clear all notifications for the authenticated student.
    """
    db.query(Notification).filter(Notification.user_id == current_user.id).delete(synchronize_session=False)
    db.commit()
    return None
