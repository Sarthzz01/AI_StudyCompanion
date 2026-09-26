"""
Personalized Daily Study Plan Service (Phase 7)
Generates structured, time-budgeted daily study routines based on
overdue spaced revisions, weak topic remediation, adaptive priorities,
and student available study time.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.learner import StudyPlanTask, LearnerModel, Progress
from app.models.study import StudySession
from app.models.material import Material
from app.services.learner_service import learner_service
from app.services.revision_service import revision_service
from app.services.adaptive_engine import adaptive_engine
from app.services.ai_service import ai_service

logger = logging.getLogger("uvicorn.error")


class StudyPlanService:
    def _find_material_for_topic(self, db: Session, canonical_topic: str) -> str:
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

    def get_or_generate_plan(
        self,
        db: Session,
        user_id: int,
        target_minutes: int = 60,
        plan_date: Optional[str] = None,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieves or dynamically generates today's time-budgeted study plan.
        Respects target_minutes budget without exceeding available hours.
        """
        now = datetime.utcnow()
        if not plan_date:
            plan_date = now.strftime("%Y-%m-%d")

        # Check existing persisted tasks for today
        if not force_regenerate:
            existing_tasks = (
                db.query(StudyPlanTask)
                .filter(
                    StudyPlanTask.user_id == user_id,
                    StudyPlanTask.plan_date == plan_date
                )
                .order_by(StudyPlanTask.order_index.asc(), StudyPlanTask.id.asc())
                .all()
            )
            if existing_tasks:
                items = [self._format_task(t) for t in existing_tasks]
                allocated = sum(t.duration_minutes for t in existing_tasks)
                completed_count = sum(1 for t in existing_tasks if t.completed)
                
                # Fetch AI guidance
                guidance = ai_service.generate_study_plan_guidance(items)

                return {
                    "plan_date": plan_date,
                    "target_minutes": target_minutes,
                    "allocated_minutes": allocated,
                    "completed_count": completed_count,
                    "total_tasks": len(existing_tasks),
                    "ai_guidance": guidance,
                    "tasks": items
                }

        # Clean existing uncompleted tasks if force regenerating
        db.query(StudyPlanTask).filter(
            StudyPlanTask.user_id == user_id,
            StudyPlanTask.plan_date == plan_date,
            StudyPlanTask.completed == False
        ).delete()
        db.commit()

        # Gather Candidate Tasks
        due_revisions = revision_service.get_due_revisions(db, user_id, now)
        all_recs = adaptive_engine.get_all_recommendations(db, user_id)
        learner_models = db.query(LearnerModel).filter(LearnerModel.user_id == user_id).all()
        lms_by_topic = {lm.topic: lm for lm in learner_models}

        candidate_tasks: List[Dict[str, Any]] = []
        seen_topics = set()

        # 1. Tier 1: Spaced Revisions Due / Overdue
        for r in due_revisions:
            topic = r["topic"]
            mat_id = r.get("material_id") or self._find_material_for_topic(db, topic)
            candidate_tasks.append({
                "task_title": f"Spaced Revision: {topic}",
                "topic": topic,
                "material_id": mat_id,
                "activity": "flashcards" if r.get("recall_reliability", 0.5) < 0.60 else "quiz",
                "duration_minutes": 15,
                "priority": "high",
                "difficulty": "medium",
                "reason": f"Spaced repetition due ({r['status']}). Reinforce retention to reset forgetting curve.",
                "action_url": f"/flashcards?material={mat_id}&topic={topic}" if r.get("recall_reliability", 0.5) < 0.60 else f"/quizzes?material={mat_id}&topic={topic}&difficulty=medium"
            })
            seen_topics.add(topic)

        # 2. Tier 2: Adaptive Recommendations (Weak / Challenging topics)
        for rec in all_recs:
            topic = rec["topic"]
            if topic in seen_topics:
                continue

            mat_id = rec.get("material_id") or self._find_material_for_topic(db, topic)
            act = rec.get("recommended_activity", "quiz")
            diff = rec.get("recommended_difficulty", "medium")
            dur = 25 if act == "summary" else (20 if act == "quiz" else 15)

            candidate_tasks.append({
                "task_title": rec["title"],
                "topic": topic,
                "material_id": mat_id,
                "activity": act,
                "duration_minutes": dur,
                "priority": rec["priority"],
                "difficulty": diff,
                "reason": rec["reason"],
                "action_url": rec["to"]
            })
            seen_topics.add(topic)

        # 3. Tier 3: AI Tutor Inquiry Reinforcement for weakest topic
        weak_topics = [lm for lm in learner_models if lm.mastery < 55.0]
        if weak_topics:
            w_top = weak_topics[0].topic
            mat_id = self._find_material_for_topic(db, w_top)
            candidate_tasks.append({
                "task_title": f"Ask AI Tutor: {w_top}",
                "topic": w_top,
                "material_id": mat_id,
                "activity": "tutor",
                "duration_minutes": 10,
                "priority": "medium",
                "difficulty": "easy",
                "reason": f"Clarify misconceptions on {w_top} directly with your interactive AI Tutor.",
                "action_url": f"/tutor"
            })

        # Time Budget Allocation (Greedy selection up to target_minutes)
        allocated_minutes = 0
        allocated_tasks = []

        # Sort candidate tasks: high priority first, then medium, then low
        priority_order = {"high": 0, "medium": 1, "low": 2}
        candidate_tasks.sort(key=lambda x: priority_order.get(x["priority"], 1))

        for cand in candidate_tasks:
            # Check if adding this task fits within study time budget
            if (allocated_minutes + cand["duration_minutes"]) <= target_minutes:
                allocated_tasks.append(cand)
                allocated_minutes += cand["duration_minutes"]
            elif allocated_minutes < (target_minutes - 10) and cand["duration_minutes"] > (target_minutes - allocated_minutes):
                # Adjust duration if small remainder
                adjusted_dur = target_minutes - allocated_minutes
                cand["duration_minutes"] = max(10, adjusted_dur)
                allocated_tasks.append(cand)
                allocated_minutes += cand["duration_minutes"]
                break

        # If target budget is very small (e.g. 15m), ensure at least 1 task
        if not allocated_tasks and candidate_tasks:
            first_task = candidate_tasks[0]
            first_task["duration_minutes"] = min(target_minutes, first_task["duration_minutes"])
            allocated_tasks.append(first_task)
            allocated_minutes = first_task["duration_minutes"]

        # Persist generated plan tasks into database
        saved_tasks = []
        for idx, t_data in enumerate(allocated_tasks):
            task_obj = StudyPlanTask(
                user_id=user_id,
                plan_date=plan_date,
                task_title=t_data["task_title"],
                topic=t_data["topic"],
                material_id=t_data["material_id"],
                activity=t_data["activity"],
                duration_minutes=t_data["duration_minutes"],
                priority=t_data["priority"],
                difficulty=t_data["difficulty"],
                completed=False,
                reason=t_data["reason"],
                action_url=t_data["action_url"],
                order_index=idx,
                created_at=now,
                updated_at=now
            )
            db.add(task_obj)
            saved_tasks.append(task_obj)

        db.commit()
        for st in saved_tasks:
            db.refresh(st)

        items = [self._format_task(st) for st in saved_tasks]
        guidance = ai_service.generate_study_plan_guidance(items)

        return {
            "plan_date": plan_date,
            "target_minutes": target_minutes,
            "allocated_minutes": allocated_minutes,
            "completed_count": 0,
            "total_tasks": len(items),
            "ai_guidance": guidance,
            "tasks": items
        }

    def complete_task(self, db: Session, user_id: int, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Marks a planned study task completed and credits study time to progress.
        """
        task = (
            db.query(StudyPlanTask)
            .filter(
                StudyPlanTask.id == task_id,
                StudyPlanTask.user_id == user_id
            )
            .first()
        )
        if not task:
            return None

        now = datetime.utcnow()
        task.completed = True
        task.completed_at = now
        task.updated_at = now

        # Record study session
        session = StudySession(
            user_id=user_id,
            material_id=task.material_id,
            duration_minutes=task.duration_minutes,
            session_type=task.activity,
            topic=task.topic,
            start_time=now - timedelta(minutes=task.duration_minutes),
            end_time=now
        )
        db.add(session)

        # Update Progress study time and last_active
        progress = db.query(Progress).filter(Progress.user_id == user_id).first()
        if not progress:
            progress = Progress(
                user_id=user_id,
                total_study_time_minutes=task.duration_minutes,
                overall_accuracy=0.0,
                questions_attempted=0,
                quizzes_completed=0,
                current_streak_days=1,
                last_active=now,
                history_json=[]
            )
            db.add(progress)
        else:
            progress.total_study_time_minutes = (progress.total_study_time_minutes or 0) + task.duration_minutes
            progress.last_active = now

        db.commit()
        db.refresh(task)
        return self._format_task(task)

    def _format_task(self, t: StudyPlanTask) -> Dict[str, Any]:
        return {
            "id": t.id,
            "task_title": t.task_title,
            "topic": t.topic,
            "material_id": t.material_id or "data-structures",
            "activity": t.activity,
            "duration_minutes": t.duration_minutes,
            "priority": t.priority,
            "difficulty": t.difficulty,
            "completed": t.completed,
            "completed_at": t.completed_at.strftime("%Y-%m-%d %H:%M") if t.completed_at else None,
            "reason": t.reason or "",
            "action_url": t.action_url or f"/quizzes?material={t.material_id}&topic={t.topic}"
        }


study_plan_service = StudyPlanService()
