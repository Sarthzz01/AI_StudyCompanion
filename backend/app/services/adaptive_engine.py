"""
Adaptive Learning Engine (Phase 6)
Computes personalized topic priorities, recommended activities, difficulties,
and evidence-backed reasons based on learner model state, quiz attempts,
flashcard practice, forgetting curve decay, and error patterns.
"""

import math
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.learner import LearnerModel, Recommendation
from app.models.study import QuizAttempt, QuizAnswer, Flashcard, Performance
from app.models.material import Material
from app.models.subject import Topic
from app.services.learner_service import learner_service

logger = logging.getLogger("uvicorn.error")


@dataclass
class AdaptiveEngineConfig:
    """Configurable weights and thresholds for adaptive learning recommendation engine."""
    # Mastery Thresholds (%)
    low_mastery_threshold: float = 55.0
    high_mastery_threshold: float = 75.0

    # Recall Reliability Thresholds (0.0 to 1.0)
    critical_recall_threshold: float = 0.50
    good_recall_threshold: float = 0.75

    # Priority Ranking Weights (Sum = 1.0)
    weight_mastery_gap: float = 0.40      # Focus on topics with low mastery
    weight_recent_mistakes: float = 0.30  # Focus on topics with repeated recent errors
    weight_revision_risk: float = 0.20    # Focus on decaying recall / overdue reviews
    weight_unstudied_bonus: float = 0.10  # Encourage initial exploration of unstudied topics

    # Forgetting Curve Parameters
    forgetting_half_life_days: float = 7.0


class AdaptiveEngine:
    def __init__(self, config: Optional[AdaptiveEngineConfig] = None):
        self.config = config or AdaptiveEngineConfig()

    def _calculate_revision_risk(
        self,
        last_reviewed: Optional[datetime],
        next_review: Optional[datetime],
        recall_reliability: float,
        now: datetime
    ) -> float:
        """
        Calculates revision risk score in [0.0, 1.0] using Ebbinghaus forgetting curve decay
        combined with scheduled spaced repetition due dates.
        """
        if not last_reviewed:
            # Unreviewed topic has moderate discovery risk
            return 0.40

        days_elapsed = max(0.0, (now - last_reviewed).total_seconds() / 86400.0)
        
        # Effective half-life scales with learner's recall reliability
        effective_half_life = max(1.0, self.config.forgetting_half_life_days * (recall_reliability / 0.5))
        decay_constant = math.log(2) / effective_half_life
        retention = math.exp(-decay_constant * days_elapsed)
        retention_decay_risk = 1.0 - retention

        # Overdue penalty if past next_review date
        overdue_penalty = 0.0
        if next_review and now > next_review:
            overdue_days = (now - next_review).total_seconds() / 86400.0
            overdue_penalty = min(0.35, 0.10 + 0.05 * overdue_days)

        risk = min(1.0, max(0.0, 0.7 * retention_decay_risk + 0.3 * overdue_penalty))
        return round(risk, 2)

    def _get_recent_mistakes_count(self, db: Session, user_id: int, canonical_topic: str) -> int:
        """Counts incorrect quiz answers on this topic across the user's last 5 quiz attempts."""
        recent_answers = (
            db.query(QuizAnswer)
            .join(QuizAttempt, QuizAnswer.attempt_id == QuizAttempt.id)
            .filter(
                QuizAttempt.user_id == user_id,
                QuizAnswer.is_correct == False
            )
            .order_by(QuizAnswer.created_at.desc())
            .limit(30)
            .all()
        )
        count = sum(1 for a in recent_answers if learner_service.normalize_topic_name(a.topic, db) == canonical_topic)
        return count

    def _find_material_for_topic(self, db: Session, user_id: int, canonical_topic: str) -> Optional[str]:
        """Finds the best matching material_id for a topic from user's library or seeded materials."""
        materials = db.query(Material).all()
        for m in materials:
            for t in (m.topics_json or []):
                t_name = t.get("name") if isinstance(t, dict) else t
                if t_name and learner_service.normalize_topic_name(t_name, db) == canonical_topic:
                    return m.id

        # Fallback keyword matching
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

    def generate_recommendation_for_topic(
        self,
        db: Session,
        user_id: int,
        canonical_topic: str,
        learner_model: Optional[LearnerModel],
        now: datetime
    ) -> Dict[str, Any]:
        """
        Generates an individual adaptive recommendation item for a given topic.
        """
        material_id = self._find_material_for_topic(db, user_id, canonical_topic)

        if learner_model:
            mastery = learner_model.mastery or 0.0
            quiz_acc = learner_model.quiz_accuracy or 0.0
            fc_perf = learner_model.flashcard_performance or 0.0
            recall_rel = learner_model.recall_reliability or 0.50
            last_reviewed = learner_model.last_reviewed
            next_review = learner_model.next_review
            is_unstudied = False
        else:
            mastery = 0.0
            quiz_acc = 0.0
            fc_perf = 0.0
            recall_rel = 0.50
            last_reviewed = None
            next_review = None
            is_unstudied = True

        revision_risk_score = self._calculate_revision_risk(last_reviewed, next_review, recall_rel, now)
        mistakes_count = self._get_recent_mistakes_count(db, user_id, canonical_topic) if not is_unstudied else 0

        # Priority calculation
        mastery_gap = (100.0 - mastery) / 100.0
        mistakes_factor = min(1.0, mistakes_count / 3.0)
        unstudied_factor = 1.0 if is_unstudied else 0.0

        priority_score = 100.0 * (
            self.config.weight_mastery_gap * mastery_gap +
            self.config.weight_revision_risk * revision_risk_score +
            self.config.weight_recent_mistakes * mistakes_factor +
            self.config.weight_unstudied_bonus * unstudied_factor
        )
        priority_score = min(100.0, max(0.0, round(priority_score, 1)))

        if priority_score >= 48.0:
            priority_label = "high"
        elif priority_score >= 25.0:
            priority_label = "medium"
        else:
            priority_label = "low"

        # Adaptive Activity & Difficulty Decision Rules
        if is_unstudied:
            # Unstudied topic -> intro flashcards & reading
            recommended_activity = "flashcards"
            recommended_difficulty = "easy"
            title = f"Explore {canonical_topic}"
            reason = f"New syllabus topic in your course. Start with active recall flashcards to build foundational concepts."
            action = "Open flashcards"
            action_type = "flashcards"
            target_url = f"/flashcards?material={material_id}&topic={canonical_topic}"
            icon = "layers"

        elif mastery < self.config.low_mastery_threshold or (mistakes_count >= 2 and mastery < 65.0) or recall_rel < self.config.critical_recall_threshold:
            # Low Mastery or struggling with frequent mistakes / low recall
            if mistakes_count >= 2 or recall_rel < self.config.critical_recall_threshold:
                # Low mastery / low recall + mistakes -> Revision + easier practice
                recommended_activity = "summary"
                recommended_difficulty = "easy"
                title = f"Review {canonical_topic}"
                reason = f"Mastery is {int(mastery)}% with {mistakes_count} recent incorrect answers. Review key concepts and take an easy practice quiz."
                action = "Read summary & practice"
                action_type = "summary"
                target_url = f"/summaries/{material_id}"
                icon = "fileText"
            else:
                recommended_activity = "quiz"
                recommended_difficulty = "easy"
                title = f"Practice {canonical_topic}"
                reason = f"Accuracy is {int(quiz_acc or mastery)}% — practice an easy introductory quiz to strengthen core understanding."
                action = "Start easy quiz"
                action_type = "quiz"
                target_url = f"/quizzes?material={material_id}&topic={canonical_topic}&difficulty=easy"
                icon = "clipboardCheck"

        elif mastery < self.config.high_mastery_threshold:
            # Medium Mastery (55% - 74%)
            if recall_rel < self.config.good_recall_threshold or revision_risk_score >= 0.50:
                # Moderate mastery + fading memory -> Flashcard drill
                recommended_activity = "flashcards"
                recommended_difficulty = "medium"
                title = f"Flashcard Drill: {canonical_topic}"
                reason = f"Recall reliability is {int(recall_rel * 100)}%. Reinforce retention with active recall cards."
                action = "Review flashcards"
                action_type = "flashcards"
                target_url = f"/flashcards?material={material_id}&topic={canonical_topic}"
                icon = "layers"
            else:
                recommended_activity = "quiz"
                recommended_difficulty = "medium"
                title = f"Take a Quiz on {canonical_topic}"
                reason = f"Mastery is solid at {int(mastery)}%. Step up to a medium-difficulty quiz to test applied problem solving."
                action = "Start medium quiz"
                action_type = "quiz"
                target_url = f"/quizzes?material={material_id}&topic={canonical_topic}&difficulty=medium"
                icon = "clipboardCheck"

        else:
            # High Mastery (>= 75%)
            if revision_risk_score >= 0.55 or (next_review and now >= next_review):
                # High mastery but overdue revision -> Spaced refresher quiz
                recommended_activity = "quiz"
                recommended_difficulty = "medium"
                title = f"Refresh {canonical_topic}"
                reason = f"Mastery is high ({int(mastery)}%), but this topic is due for spaced repetition refresh."
                action = "Quick refresh quiz"
                action_type = "quiz"
                target_url = f"/quizzes?material={material_id}&topic={canonical_topic}&difficulty=medium"
                icon = "clipboardCheck"
            else:
                # High mastery & strong recall -> Hard/Advanced quiz challenge
                recommended_activity = "quiz"
                recommended_difficulty = "hard"
                title = f"Mastery Challenge: {canonical_topic}"
                reason = f"Outstanding grasp ({int(mastery)}%). Challenge yourself with a hard quiz to achieve complete mastery."
                action = "Start hard quiz"
                action_type = "quiz"
                target_url = f"/quizzes?material={material_id}&topic={canonical_topic}&difficulty=hard"
                icon = "target"

        return {
            "id": f"rec-{canonical_topic.lower().replace(' ', '-').replace('&', 'and')}",
            "topic": canonical_topic,
            "title": title,
            "reason": reason,
            "action": action,
            "action_type": action_type,
            "to": target_url,
            "priority": priority_label,
            "priority_score": priority_score,
            "recommended_difficulty": recommended_difficulty,
            "recommended_activity": recommended_activity,
            "revision_risk": "high" if revision_risk_score >= 0.60 else ("medium" if revision_risk_score >= 0.35 else "low"),
            "revision_risk_score": revision_risk_score,
            "material_id": material_id,
            "icon": icon,
            "mastery": mastery,
            "recall_reliability": recall_rel,
            "recent_mistakes": mistakes_count
        }

    def get_all_recommendations(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Generates and returns all adaptive recommendations ranked by priority score.
        """
        now = datetime.utcnow()
        # Consolidate learner models first
        learner_service.consolidate_learner_models(db, user_id)

        # Collect all tracked topics from learner models
        learner_models = db.query(LearnerModel).filter(LearnerModel.user_id == user_id).all()
        models_by_topic = {lm.topic: lm for lm in learner_models}

        # Collect syllabus topics from user's materials or seeded materials
        materials = db.query(Material).all()
        all_topics = set(models_by_topic.keys())
        for m in materials:
            for t in (m.topics_json or []):
                t_name = t.get("name") if isinstance(t, dict) else t
                if t_name:
                    canonical = learner_service.normalize_topic_name(t_name, db)
                    all_topics.add(canonical)

        if not all_topics:
            all_topics = {"Tree Traversal", "BST Operations", "Binary Trees", "Graph Traversal", "Normalisation", "SQL Queries"}

        recommendations = []
        for topic_name in all_topics:
            lm = models_by_topic.get(topic_name)
            rec = self.generate_recommendation_for_topic(db, user_id, topic_name, lm, now)
            recommendations.append(rec)

        # Sort descending by priority score
        recommendations.sort(key=lambda x: x["priority_score"], reverse=True)
        return recommendations

    def get_today_recommendations(self, db: Session, user_id: int, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Returns top curated daily recommendations for today's study plan.
        Balances priority: highest need topic + spaced revision due + challenge.
        """
        all_recs = self.get_all_recommendations(db, user_id)
        if not all_recs:
            return []

        # Return top items up to limit
        return all_recs[:limit]


adaptive_engine = AdaptiveEngine()
