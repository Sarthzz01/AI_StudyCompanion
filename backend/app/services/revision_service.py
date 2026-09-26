"""
SM-2 Spaced Repetition Revision Service (Phase 7)
Implements SuperMemo SM-2 algorithm to schedule spaced revisions based on
student performance quality, ease factor, and recall history.
"""

import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.learner import RevisionSchedule, LearnerModel
from app.models.subject import Topic
from app.models.material import Material
from app.services.learner_service import learner_service

logger = logging.getLogger("uvicorn.error")


class RevisionService:
    @staticmethod
    def calculate_sm2(
        quality: int,
        previous_ease_factor: float = 2.5,
        previous_interval: int = 1,
        repetition_count: int = 0
    ) -> Tuple[int, float, int]:
        """
        SuperMemo SM-2 Algorithm implementation.
        Quality q in [0, 5]:
          5: perfect response
          4: correct response after hesitation
          3: correct response with serious difficulty
          2: incorrect response where correct seemed easy to recall
          1: incorrect response where correct was remembered
          0: complete blackout

        Returns: (interval_days, new_ease_factor, new_repetition_count)
        """
        q = max(0, min(5, quality))
        
        # Calculate new Ease Factor
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = previous_ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = max(1.3, round(new_ef, 2))  # SM-2 minimum ease factor is 1.3

        if q < 3:
            # If quality < 3, reset repetitions and review tomorrow
            new_rep = 1
            new_interval = 1
        else:
            new_rep = repetition_count + 1
            if new_rep == 1:
                new_interval = 1
            elif new_rep == 2:
                new_interval = 6
            else:
                new_interval = max(1, int(round(previous_interval * new_ef)))

        return new_interval, new_ef, new_rep

    def _find_material_for_topic(self, db: Session, canonical_topic: str) -> Optional[str]:
        materials = db.query(Material).all()
        for m in materials:
            for t in (m.topics_json or []):
                t_name = t.get("name") if isinstance(t, dict) else t
                if t_name and learner_service.normalize_topic_name(t_name, db) == canonical_topic:
                    return m.id

        topic_lower = canonical_topic.lower()
        if any(k in topic_lower for k in ["tree", "graph", "array", "stack", "sort", "hash"]):
            return "data-structures"
        elif any(k in topic_lower for k in ["sql", "relational", "normali", "er model", "transaction", "index"]):
            return "dbms"
        elif any(k in topic_lower for k in ["process", "thread", "scheduling", "deadlock", "memory", "paging", "file"]):
            return "operating-systems"
        elif any(k in topic_lower for k in ["osi", "tcp", "udp", "routing", "ip", "protocol", "network", "signal", "link"]):
            return "computer-networks"

        return materials[0].id if materials else "data-structures"

    def record_topic_revision(
        self,
        db: Session,
        user_id: int,
        topic_name: str,
        quality: int,
        material_id: Optional[str] = None
    ) -> RevisionSchedule:
        """
        Records/updates a spaced repetition revision schedule item for a topic.
        Syncs next_review date with LearnerModel.
        """
        canonical_topic = learner_service.normalize_topic_name(topic_name, db)
        topic_obj = db.query(Topic).filter(Topic.name == canonical_topic).first()
        topic_id = topic_obj.id if topic_obj else None
        
        if not material_id:
            material_id = self._find_material_for_topic(db, canonical_topic)

        now = datetime.utcnow()
        schedule = (
            db.query(RevisionSchedule)
            .filter(
                RevisionSchedule.user_id == user_id,
                RevisionSchedule.topic_name == canonical_topic
            )
            .first()
        )

        prev_ef = schedule.ease_factor if schedule else 2.5
        prev_interval = schedule.interval_days if schedule else 1
        prev_rep = schedule.repetition_count if schedule else 0

        interval_days, new_ef, new_rep = self.calculate_sm2(
            quality=quality,
            previous_ease_factor=prev_ef,
            previous_interval=prev_interval,
            repetition_count=prev_rep
        )

        next_date = now + timedelta(days=interval_days)

        if not schedule:
            schedule = RevisionSchedule(
                user_id=user_id,
                topic_id=topic_id,
                topic_name=canonical_topic,
                material_id=material_id,
                scheduled_date=next_date,
                status="pending",
                interval_days=interval_days,
                repetition_count=new_rep,
                ease_factor=new_ef,
                last_reviewed=now,
                created_at=now,
                updated_at=now
            )
            db.add(schedule)
        else:
            schedule.scheduled_date = next_date
            schedule.interval_days = interval_days
            schedule.repetition_count = new_rep
            schedule.ease_factor = new_ef
            schedule.status = "pending"
            schedule.last_reviewed = now
            schedule.updated_at = now
            if topic_id:
                schedule.topic_id = topic_id
            if material_id:
                schedule.material_id = material_id

        # Sync LearnerModel next_review
        lm = db.query(LearnerModel).filter(
            LearnerModel.user_id == user_id,
            LearnerModel.topic == canonical_topic
        ).first()
        if lm:
            lm.last_reviewed = now
            lm.next_review = next_date

        db.commit()
        db.refresh(schedule)
        return schedule

    def update_revision_after_quiz(
        self,
        db: Session,
        user_id: int,
        topic_name: str,
        score: int,
        total: int,
        material_id: Optional[str] = None
    ) -> RevisionSchedule:
        """Translates quiz score into SM-2 quality [0..5] and updates revision schedule."""
        acc = (score / total) if total > 0 else 0.0
        if acc >= 0.90:
            quality = 5
        elif acc >= 0.75:
            quality = 4
        elif acc >= 0.55:
            quality = 3
        elif acc >= 0.35:
            quality = 2
        elif acc > 0:
            quality = 1
        else:
            quality = 0
        return self.record_topic_revision(db, user_id, topic_name, quality, material_id)

    def update_revision_after_flashcard(
        self,
        db: Session,
        user_id: int,
        topic_name: str,
        rating: str,
        material_id: Optional[str] = None
    ) -> RevisionSchedule:
        """Translates flashcard rating (easy=5, medium=3, hard=1) into SM-2 quality and updates revision schedule."""
        rating_map = {"easy": 5, "medium": 3, "hard": 1}
        quality = rating_map.get(rating.lower().strip(), 3)
        return self.record_topic_revision(db, user_id, topic_name, quality, material_id)

    def get_due_revisions(self, db: Session, user_id: int, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all topics currently due or overdue for spaced revision.
        Combines RevisionSchedule records and LearnerModel states.
        """
        if not now:
            now = datetime.utcnow()

        schedules = (
            db.query(RevisionSchedule)
            .filter(
                RevisionSchedule.user_id == user_id,
                RevisionSchedule.scheduled_date <= now
            )
            .order_by(RevisionSchedule.scheduled_date.asc())
            .all()
        )

        results = []
        seen_topics = set()
        for s in schedules:
            lm = db.query(LearnerModel).filter(
                LearnerModel.user_id == user_id,
                LearnerModel.topic == s.topic_name
            ).first()

            rel = lm.recall_reliability if lm else 0.50
            diff = lm.difficulty if (lm and lm.difficulty) else ("easy" if (lm and lm.mastery < 55) else ("hard" if (lm and lm.mastery >= 75) else "medium"))
            results.append({
                "id": s.id,
                "topic": s.topic_name,
                "material_id": s.material_id or "data-structures",
                "scheduled_date": s.scheduled_date.strftime("%Y-%m-%d"),
                "interval_days": s.interval_days,
                "ease_factor": s.ease_factor,
                "repetition_count": s.repetition_count,
                "mastery": lm.mastery if lm else 50.0,
                "recall_reliability": rel,
                "retention_estimate": int(round(rel * 100)),
                "difficulty": diff,
                "status": "overdue" if s.scheduled_date < now.replace(hour=0, minute=0, second=0) else "due_today",
                "is_due": True,
                "last_reviewed": s.last_reviewed.strftime("%Y-%m-%d %H:%M") if s.last_reviewed else None
            })
            seen_topics.add(s.topic_name)

        # Check any LearnerModel records with low recall or overdue next_review not yet in RevisionSchedule
        lms = (
            db.query(LearnerModel)
            .filter(
                LearnerModel.user_id == user_id,
                (LearnerModel.next_review <= now) | (LearnerModel.recall_reliability < 0.55)
            )
            .all()
        )
        for lm in lms:
            if lm.topic not in seen_topics:
                mat_id = self._find_material_for_topic(db, lm.topic)
                diff = lm.difficulty if lm.difficulty else ("easy" if lm.mastery < 55 else ("hard" if lm.mastery >= 75 else "medium"))
                results.append({
                    "id": f"lm-{lm.id}",
                    "topic": lm.topic,
                    "material_id": mat_id,
                    "scheduled_date": lm.next_review.strftime("%Y-%m-%d") if lm.next_review else now.strftime("%Y-%m-%d"),
                    "interval_days": 1,
                    "ease_factor": 2.5,
                    "repetition_count": 1,
                    "mastery": lm.mastery,
                    "recall_reliability": lm.recall_reliability,
                    "retention_estimate": int(round(lm.recall_reliability * 100)),
                    "difficulty": diff,
                    "status": "overdue" if (lm.next_review and lm.next_review < now) else "due_today",
                    "is_due": True,
                    "last_reviewed": lm.last_reviewed.strftime("%Y-%m-%d %H:%M") if lm.last_reviewed else None
                })
                seen_topics.add(lm.topic)

        return results

    def get_all_revisions(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Retrieves all scheduled topic revisions for calendar and schedule views."""
        now = datetime.utcnow()
        schedules = (
            db.query(RevisionSchedule)
            .filter(RevisionSchedule.user_id == user_id)
            .order_by(RevisionSchedule.scheduled_date.asc())
            .all()
        )

        results = []
        for s in schedules:
            lm = db.query(LearnerModel).filter(
                LearnerModel.user_id == user_id,
                LearnerModel.topic == s.topic_name
            ).first()

            is_overdue = s.scheduled_date < now.replace(hour=0, minute=0, second=0)
            is_today = s.scheduled_date.date() == now.date()
            status_str = "overdue" if is_overdue else ("due_today" if is_today else "upcoming")
            rel = lm.recall_reliability if lm else 0.50
            diff = lm.difficulty if (lm and lm.difficulty) else ("easy" if (lm and lm.mastery < 55) else ("hard" if (lm and lm.mastery >= 75) else "medium"))

            results.append({
                "id": s.id,
                "topic": s.topic_name,
                "material_id": s.material_id or "data-structures",
                "scheduled_date": s.scheduled_date.strftime("%Y-%m-%d"),
                "interval_days": s.interval_days,
                "ease_factor": s.ease_factor,
                "repetition_count": s.repetition_count,
                "mastery": lm.mastery if lm else 50.0,
                "recall_reliability": rel,
                "retention_estimate": int(round(rel * 100)),
                "difficulty": diff,
                "status": status_str,
                "is_due": is_overdue or is_today,
                "last_reviewed": s.last_reviewed.strftime("%Y-%m-%d %H:%M") if s.last_reviewed else None
            })

        return results


revision_service = RevisionService()
calculate_sm2 = RevisionService.calculate_sm2
