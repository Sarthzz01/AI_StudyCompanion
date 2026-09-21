import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.learner import LearnerModel, Progress
from app.models.study import QuizAttempt, StudySession, Performance
from app.models.subject import Topic
from app.models.material import Material

logger = logging.getLogger("uvicorn.error")

CANONICAL_TOPIC_MAP = {
    # Data Structures
    "tree traversal": "Tree Traversal",
    "tree traversals": "Tree Traversal",
    "binary tree traversal": "Tree Traversal",
    "binary tree traversals": "Tree Traversal",
    "binary tree traversals and reconstruction": "Tree Traversal",
    "tree reconstruction": "Tree Traversal",
    "inorder traversal": "Tree Traversal",
    "preorder traversal": "Tree Traversal",
    "postorder traversal": "Tree Traversal",
    "level order traversal": "Tree Traversal",
    "level-order traversal": "Tree Traversal",

    "bst operations": "BST Operations",
    "bst": "BST Operations",
    "binary search trees": "BST Operations",
    "binary search tree": "BST Operations",
    "binary search tree operations": "BST Operations",
    "binary search tree deletion algorithms": "BST Operations",
    "bst deletion": "BST Operations",
    "bst insertion": "BST Operations",

    "binary trees": "Binary Trees",
    "binary tree": "Binary Trees",
    "binary trees and bst fundamentals": "Binary Trees",
    "binary tree fundamentals": "Binary Trees",
    "binary tree properties": "Binary Trees",

    "graph traversal": "Graph Traversal",
    "graph traversals": "Graph Traversal",
    "graph representations and breadth-first search (bfs)": "Graph Traversal",
    "depth-first search (dfs) and graph algorithms": "Graph Traversal",
    "breadth-first search": "Graph Traversal",
    "depth-first search": "Graph Traversal",
    "bfs": "Graph Traversal",
    "dfs": "Graph Traversal",
    "graph algorithms": "Graph Traversal",
    "graph representations": "Graph Traversal",
    "topological sort": "Graph Traversal",

    "arrays & linked lists": "Arrays & Linked Lists",
    "arrays and linked lists": "Arrays & Linked Lists",
    "arrays": "Arrays & Linked Lists",
    "array": "Arrays & Linked Lists",
    "linked lists": "Arrays & Linked Lists",
    "linked list": "Arrays & Linked Lists",
    "singly linked list": "Arrays & Linked Lists",
    "doubly linked list": "Arrays & Linked Lists",

    "stacks & queues": "Stacks & Queues",
    "stacks and queues": "Stacks & Queues",
    "stack": "Stacks & Queues",
    "stacks": "Stacks & Queues",
    "queue": "Stacks & Queues",
    "queues": "Stacks & Queues",

    "hashing": "Hashing",
    "hash tables": "Hashing",
    "hash table": "Hashing",
    "hash map": "Hashing",
    "hashing and collision resolution": "Hashing",
    "collision resolution": "Hashing",

    "sorting & searching": "Sorting & Searching",
    "sorting and searching": "Sorting & Searching",
    "sorting": "Sorting & Searching",
    "searching": "Sorting & Searching",
    "sorting algorithms": "Sorting & Searching",
    "searching algorithms": "Sorting & Searching",

    # DBMS
    "er modelling": "ER Modelling",
    "er modeling": "ER Modelling",
    "entity relationship": "ER Modelling",
    "entity-relationship modeling": "ER Modelling",
    "er diagrams": "ER Modelling",
    "er diagram": "ER Modelling",

    "relational algebra": "Relational Algebra",
    "relational data model and integrity constraints": "Relational Algebra",
    "relational model": "Relational Algebra",
    "relational calculus": "Relational Algebra",
    "integrity constraints": "Relational Algebra",

    "sql queries": "SQL Queries",
    "sql": "SQL Queries",
    "structured query language": "SQL Queries",
    "sql query": "SQL Queries",
    "sql joins": "SQL Queries",

    "normalisation": "Normalisation",
    "normalization": "Normalisation",
    "database normalization and normal forms": "Normalisation",
    "database normalization": "Normalisation",
    "normal forms": "Normalisation",
    "1nf": "Normalisation",
    "2nf": "Normalisation",
    "3nf": "Normalisation",
    "bcnf": "Normalisation",

    "transactions & acid": "Transactions & ACID",
    "transactions and acid": "Transactions & ACID",
    "transaction processing and acid guarantees": "Transactions & ACID",
    "transactions": "Transactions & ACID",
    "transaction": "Transactions & ACID",
    "acid properties": "Transactions & ACID",
    "acid guarantees": "Transactions & ACID",
    "transaction processing": "Transactions & ACID",

    "indexing": "Indexing",
    "b-trees": "Indexing",
    "b+ trees": "Indexing",
    "b-tree indexing": "Indexing",
    "database indexing": "Indexing",

    "concurrency control": "Concurrency Control",
    "two-phase locking": "Concurrency Control",
    "2pl": "Concurrency Control",
    "strict 2pl": "Concurrency Control",

    # OS
    "processes & threads": "Processes & Threads",
    "processes and threads": "Processes & Threads",
    "process management": "Processes & Threads",
    "threads": "Processes & Threads",
    "multithreading": "Processes & Threads",

    "cpu scheduling": "CPU Scheduling",
    "cpu scheduling algorithms": "CPU Scheduling",
    "scheduling algorithms": "CPU Scheduling",

    "synchronisation": "Synchronisation",
    "synchronization": "Synchronisation",
    "process synchronization": "Synchronisation",
    "critical section": "Synchronisation",
    "semaphores": "Synchronisation",
    "mutex": "Synchronisation",

    "deadlocks": "Deadlocks",
    "deadlock": "Deadlocks",
    "banker's algorithm": "Deadlocks",
    "deadlock detection": "Deadlocks",

    "memory management": "Memory Management",
    "virtual memory": "Memory Management",
    "paging": "Memory Management",
    "segmentation": "Memory Management",
    "page replacement": "Memory Management",

    "file systems": "File Systems",
    "file system": "File Systems",
    "inodes": "File Systems",
    "directory structure": "File Systems",

    # Computer Networks
    "osi & tcp/ip models": "OSI & TCP/IP Models",
    "osi and tcp/ip models": "OSI & TCP/IP Models",
    "osi model": "OSI & TCP/IP Models",
    "tcp/ip model": "OSI & TCP/IP Models",

    "data link layer": "Data Link Layer",
    "framing": "Data Link Layer",
    "error detection": "Data Link Layer",
    "crc": "Data Link Layer",

    "routing algorithms": "Routing Algorithms",
    "dijkstra": "Routing Algorithms",
    "distance vector": "Routing Algorithms",
    "link state": "Routing Algorithms",
    "routing": "Routing Algorithms",

    "tcp & udp": "TCP & UDP",
    "tcp and udp": "TCP & UDP",
    "tcp": "TCP & UDP",
    "udp": "TCP & UDP",
    "transmission control protocol": "TCP & UDP",
    "user datagram protocol": "TCP & UDP",

    "congestion control": "Congestion Control",
    "tcp congestion control": "Congestion Control",

    "application protocols": "Application Protocols",
    "http": "Application Protocols",
    "https": "Application Protocols",
    "dns": "Application Protocols",
    "smtp": "Application Protocols",
}

class LearnerService:
    @staticmethod
    def _calculate_review_interval(mastery: float, recall_reliability: float) -> int:
        """
        Calculates optimal spaced repetition review interval (days)
        based on topic mastery and recall reliability.
        """
        if mastery >= 90.0 and recall_reliability >= 0.85:
            return 14
        elif mastery >= 75.0 and recall_reliability >= 0.70:
            return 7
        elif mastery >= 50.0 and recall_reliability >= 0.50:
            return 3
        else:
            return 1

    def normalize_topic_name(self, topic_name: Optional[str], db: Optional[Session] = None) -> str:
        """
        Normalizes AI-generated or raw subtopic names into a canonical curriculum topic name.
        Prevents duplicate LearnerModel rows for equivalent topics.
        """
        if not topic_name:
            return "General"

        cleaned = topic_name.strip()
        key = cleaned.lower()

        # 1. Exact match in canonical dictionary
        if key in CANONICAL_TOPIC_MAP:
            return CANONICAL_TOPIC_MAP[key]

        # 2. Intelligent concept and subtopic keyword rules
        if "traversal" in key and ("tree" in key or "binary" in key):
            return "Tree Traversal"
        elif "search tree" in key or "bst deletion" in key or "bst insertion" in key or "bst operation" in key:
            return "BST Operations"
        elif "bst" in key and not "traversal" in key and not "binary tree and" in key:
            return "BST Operations"
        elif "binary tree" in key and "traversal" not in key and "search tree" not in key:
            return "Binary Trees"
        elif "graph" in key or "bfs" in key or "dfs" in key or "breadth-first" in key or "depth-first" in key:
            return "Graph Traversal"
        elif "hash" in key:
            return "Hashing"
        elif "sorting" in key or "bubble sort" in key or "merge sort" in key or "quick sort" in key:
            return "Sorting & Searching"
        elif "linked list" in key or ("array" in key and "relational" not in key):
            return "Arrays & Linked Lists"
        elif "stack" in key or "queue" in key:
            return "Stacks & Queues"
        elif "normali" in key or "1nf" in key or "2nf" in key or "3nf" in key or "bcnf" in key:
            return "Normalisation"
        elif "relational" in key:
            return "Relational Algebra"
        elif "er model" in key or "entity relationship" in key:
            return "ER Modelling"
        elif "sql" in key:
            return "SQL Queries"
        elif "transaction" in key or "acid" in key:
            return "Transactions & ACID"
        elif "indexing" in key or "b-tree" in key or "b+ tree" in key:
            return "Indexing"
        elif "concurrency" in key or "2pl" in key or "locking" in key:
            return "Concurrency Control"
        elif "process" in key or "thread" in key:
            return "Processes & Threads"
        elif "scheduling" in key or "cpu" in key:
            return "CPU Scheduling"
        elif "synchroni" in key or "semaphore" in key or "mutex" in key:
            return "Synchronisation"
        elif "deadlock" in key:
            return "Deadlocks"
        elif "memory" in key or "paging" in key or "virtual memory" in key:
            return "Memory Management"
        elif "file system" in key or "inode" in key:
            return "File Systems"
        elif "osi" in key or "tcp/ip model" in key:
            return "OSI & TCP/IP Models"
        elif "data link" in key or "framing" in key or "crc" in key:
            return "Data Link Layer"
        elif "routing" in key or "dijkstra" in key:
            return "Routing Algorithms"
        elif "tcp" in key or "udp" in key:
            return "TCP & UDP"
        elif "congestion" in key:
            return "Congestion Control"
        elif "protocol" in key or "http" in key or "dns" in key:
            return "Application Protocols"

        # 3. Database lookup against seeded Topics
        if db:
            db_topics = db.query(Topic).all()
            for t in db_topics:
                if t.name.lower() == key:
                    return t.name

            # Substring / keyword overlap matching against DB topics
            for t in db_topics:
                t_words = [w for w in t.name.lower().replace('&', ' ').replace('-', ' ').split() if len(w) > 2 and w not in ('and', 'the', 'for')]
                if t_words and all(w in key for w in t_words):
                    return t.name

            key_words = [w for w in key.replace('&', ' ').replace('-', ' ').split() if len(w) > 2 and w not in ('and', 'the', 'for', 'fundamentals', 'algorithms', 'operations', 'reconstruction')]
            if key_words:
                for t in db_topics:
                    t_lower = t.name.lower()
                    if all(w in t_lower for w in key_words):
                        return t.name

        return cleaned

    def consolidate_learner_models(self, db: Session, user_id: int):
        """
        Consolidates any duplicate or non-canonical LearnerModel rows for a user.
        Preserves all historical quiz and flashcard performance.
        """
        learner_models = db.query(LearnerModel).filter(LearnerModel.user_id == user_id).all()
        if not learner_models:
            return

        # Group by normalized topic name
        by_canonical: Dict[str, List[LearnerModel]] = {}
        for lm in learner_models:
            c_name = self.normalize_topic_name(lm.topic, db)
            by_canonical.setdefault(c_name, []).append(lm)

        has_changes = False
        for c_name, models in by_canonical.items():
            topic_obj = db.query(Topic).filter(Topic.name == c_name).first()
            topic_id = topic_obj.id if topic_obj else None

            if len(models) == 1:
                lm = models[0]
                changed = False
                if lm.topic != c_name:
                    lm.topic = c_name
                    changed = True
                if topic_id and lm.topic_id != topic_id:
                    lm.topic_id = topic_id
                    changed = True
                if changed:
                    db.add(lm)
                    has_changes = True
            else:
                # Multiple models mapped to same canonical topic: merge them
                primary = None
                for m in models:
                    if m.topic == c_name:
                        primary = m
                        break
                if not primary:
                    primary = models[0]

                merged_history = []
                quiz_accs = []
                fc_perfs = []
                recalls = []
                latest_reviewed = None
                soonest_next_review = None

                for m in models:
                    if m.quiz_accuracy and m.quiz_accuracy > 0:
                        quiz_accs.append(m.quiz_accuracy)
                    if m.flashcard_performance and m.flashcard_performance > 0:
                        fc_perfs.append(m.flashcard_performance)
                    if m.recall_reliability:
                        recalls.append(m.recall_reliability)
                    if m.last_reviewed:
                        if not latest_reviewed or m.last_reviewed > latest_reviewed:
                            latest_reviewed = m.last_reviewed
                    if m.next_review:
                        if not soonest_next_review or m.next_review < soonest_next_review:
                            soonest_next_review = m.next_review
                    if m.recent_performance_json:
                        merged_history.extend(m.recent_performance_json)

                merged_history = merged_history[-15:]
                avg_quiz = round(sum(quiz_accs) / len(quiz_accs), 1) if quiz_accs else (primary.quiz_accuracy or 0.0)
                avg_fc = round(sum(fc_perfs) / len(fc_perfs), 1) if fc_perfs else (primary.flashcard_performance or 0.0)
                avg_recall = round(sum(recalls) / len(recalls), 2) if recalls else (primary.recall_reliability or 0.5)

                if avg_fc > 0:
                    new_mastery = round(0.50 * avg_quiz + 0.30 * avg_fc + 0.20 * (avg_recall * 100.0), 1)
                else:
                    new_mastery = round(0.75 * avg_quiz + 0.25 * (avg_recall * 100.0), 1)

                primary.topic = c_name
                primary.topic_id = topic_id
                primary.quiz_accuracy = avg_quiz
                primary.flashcard_performance = avg_fc
                primary.recall_reliability = avg_recall
                primary.mastery = min(100.0, max(0.0, new_mastery))
                primary.last_reviewed = latest_reviewed
                primary.next_review = soonest_next_review
                primary.recent_performance_json = merged_history
                db.add(primary)

                for m in models:
                    if m.id != primary.id:
                        db.delete(m)
                has_changes = True

        if has_changes:
            db.commit()

    def update_topic_after_quiz(
        self,
        db: Session,
        user_id: int,
        topic_name: str,
        score: int,
        total: int,
        difficulty: str = "medium"
    ) -> LearnerModel:
        """
        Updates topic LearnerModel following a completed quiz attempt.
        Calculates quiz accuracy, recall reliability, composite mastery, and next review date.
        """
        canonical_topic = self.normalize_topic_name(topic_name, db)
        topic_obj = db.query(Topic).filter(Topic.name == canonical_topic).first()
        topic_id = topic_obj.id if topic_obj else None

        attempt_acc = round((score / total * 100.0), 1) if total > 0 else 0.0

        learner = db.query(LearnerModel).filter(
            LearnerModel.user_id == user_id,
            LearnerModel.topic == canonical_topic
        ).first()

        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%d")

        if not learner:
            # First time seeing this topic
            new_quiz_acc = attempt_acc
            new_recall = min(1.0, max(0.2, round((attempt_acc / 100.0) * 0.8 + 0.1, 2)))
            new_mastery = round(0.75 * new_quiz_acc + 0.25 * (new_recall * 100.0), 1)
            history = [{"type": "quiz", "score": attempt_acc, "date": date_str}]

            interval_days = self._calculate_review_interval(new_mastery, new_recall)
            learner = LearnerModel(
                user_id=user_id,
                topic_id=topic_id,
                topic=canonical_topic,
                quiz_accuracy=new_quiz_acc,
                flashcard_performance=0.0,
                recall_reliability=new_recall,
                mastery=min(100.0, max(0.0, new_mastery)),
                difficulty="hard" if new_quiz_acc >= 80 else ("easy" if new_quiz_acc < 50 else "medium"),
                last_reviewed=now,
                next_review=now + timedelta(days=interval_days),
                recent_performance_json=history
            )
            db.add(learner)
        else:
            # Update rolling accuracy using exponential moving average
            prev_acc = learner.quiz_accuracy or 0.0
            new_quiz_acc = round(0.7 * attempt_acc + 0.3 * prev_acc, 1) if prev_acc > 0 else attempt_acc

            # Update recall reliability
            prev_recall = learner.recall_reliability or 0.5
            if attempt_acc >= 75.0:
                new_recall = min(1.0, round(0.6 * prev_recall + 0.4 * (attempt_acc / 100.0) + 0.05, 2))
            elif attempt_acc < 50.0:
                new_recall = max(0.2, round(0.7 * prev_recall + 0.3 * (attempt_acc / 100.0), 2))
            else:
                new_recall = round(0.7 * prev_recall + 0.3 * (attempt_acc / 100.0), 2)

            # Update composite mastery
            fc_perf = learner.flashcard_performance or 0.0
            if fc_perf > 0:
                new_mastery = round(0.50 * new_quiz_acc + 0.30 * fc_perf + 0.20 * (new_recall * 100.0), 1)
            else:
                new_mastery = round(0.75 * new_quiz_acc + 0.25 * (new_recall * 100.0), 1)

            # Update rolling performance history
            history = list(learner.recent_performance_json or [])
            history.append({"type": "quiz", "score": attempt_acc, "date": date_str})
            learner.recent_performance_json = history[-10:]

            learner.topic = canonical_topic
            if topic_id:
                learner.topic_id = topic_id
            learner.quiz_accuracy = new_quiz_acc
            learner.recall_reliability = new_recall
            learner.mastery = min(100.0, max(0.0, new_mastery))
            learner.difficulty = "hard" if new_quiz_acc >= 80 else ("easy" if new_quiz_acc < 50 else "medium")
            learner.last_reviewed = now

            interval_days = self._calculate_review_interval(new_mastery, new_recall)
            learner.next_review = now + timedelta(days=interval_days)

        db.commit()
        db.refresh(learner)
        return learner

    def update_topic_after_flashcard(
        self,
        db: Session,
        user_id: int,
        topic_name: str,
        rating: str
    ) -> LearnerModel:
        """
        Updates topic LearnerModel following a flashcard practice review.
        'easy' -> 100%, 'medium' -> 70%, 'hard' -> 40%.
        """
        canonical_topic = self.normalize_topic_name(topic_name, db)
        topic_obj = db.query(Topic).filter(Topic.name == canonical_topic).first()
        topic_id = topic_obj.id if topic_obj else None

        rating_scores = {"easy": 100.0, "medium": 70.0, "hard": 40.0}
        score = rating_scores.get(rating.lower(), 70.0)

        learner = db.query(LearnerModel).filter(
            LearnerModel.user_id == user_id,
            LearnerModel.topic == canonical_topic
        ).first()

        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%d")

        if not learner:
            new_fc = score
            new_recall = 0.85 if rating == "easy" else (0.65 if rating == "medium" else 0.40)
            new_mastery = round(0.70 * new_fc + 0.30 * (new_recall * 100.0), 1)
            history = [{"type": "flashcard", "rating": rating, "score": score, "date": date_str}]

            interval_days = self._calculate_review_interval(new_mastery, new_recall)
            learner = LearnerModel(
                user_id=user_id,
                topic_id=topic_id,
                topic=canonical_topic,
                quiz_accuracy=0.0,
                flashcard_performance=new_fc,
                recall_reliability=new_recall,
                mastery=min(100.0, max(0.0, new_mastery)),
                difficulty="medium",
                last_reviewed=now,
                next_review=now + timedelta(days=interval_days),
                recent_performance_json=history
            )
            db.add(learner)
        else:
            prev_fc = learner.flashcard_performance or 0.0
            new_fc = round(0.6 * score + 0.4 * prev_fc, 1) if prev_fc > 0 else score

            prev_recall = learner.recall_reliability or 0.5
            if rating == "easy":
                new_recall = min(1.0, round(prev_recall * 0.6 + 0.4 * 1.0 + 0.05, 2))
            elif rating == "medium":
                new_recall = round(prev_recall * 0.7 + 0.3 * 0.70, 2)
            else:
                new_recall = max(0.2, round(prev_recall * 0.6 + 0.4 * 0.40, 2))

            quiz_acc = learner.quiz_accuracy or 0.0
            if quiz_acc > 0:
                new_mastery = round(0.50 * quiz_acc + 0.30 * new_fc + 0.20 * (new_recall * 100.0), 1)
            else:
                new_mastery = round(0.70 * new_fc + 0.30 * (new_recall * 100.0), 1)

            history = list(learner.recent_performance_json or [])
            history.append({"type": "flashcard", "rating": rating, "score": score, "date": date_str})
            learner.recent_performance_json = history[-10:]

            learner.topic = canonical_topic
            if topic_id:
                learner.topic_id = topic_id
            learner.flashcard_performance = new_fc
            learner.recall_reliability = new_recall
            learner.mastery = min(100.0, max(0.0, new_mastery))
            learner.last_reviewed = now

            interval_days = self._calculate_review_interval(new_mastery, new_recall)
            learner.next_review = now + timedelta(days=interval_days)

        db.commit()
        db.refresh(learner)
        return learner

    def update_after_study_session(
        self,
        db: Session,
        user_id: int,
        duration_minutes: int,
        topic_name: Optional[str] = None,
        session_type: str = "reading"
    ) -> Progress:
        """
        Logs study time, updates streak/last_active, and refreshes topic review timestamp.
        """
        progress = db.query(Progress).filter(Progress.user_id == user_id).first()
        now = datetime.utcnow()

        if not progress:
            progress = Progress(
                user_id=user_id,
                overall_accuracy=0.0,
                total_study_time_minutes=duration_minutes,
                questions_attempted=0,
                quizzes_completed=0,
                current_streak_days=1,
                last_active=now,
                history_json=[]
            )
            db.add(progress)
        else:
            progress.total_study_time_minutes = (progress.total_study_time_minutes or 0) + duration_minutes
            progress.last_active = now

        if topic_name:
            canonical_topic = self.normalize_topic_name(topic_name, db)
            learner = db.query(LearnerModel).filter(
                LearnerModel.user_id == user_id,
                LearnerModel.topic == canonical_topic
            ).first()
            if learner:
                learner.last_reviewed = now
                learner.recall_reliability = min(1.0, round((learner.recall_reliability or 0.5) + 0.05, 2))

        db.commit()
        db.refresh(progress)
        return progress

    # =========================================================================
    # DETECTIONS & AGGREGATE METRICS
    # =========================================================================

    def detect_topics(self, learner_models: List[LearnerModel]) -> Dict[str, List[Any]]:
        """
        Categorizes topics into strong, weak, improving, and review-due categories.
        """
        strong = []
        weak = []
        improving = []
        needing_review = []
        now = datetime.utcnow()

        for lm in learner_models:
            effective_acc = lm.mastery if lm.mastery > 0 else (lm.quiz_accuracy or 0.0)

            # Strong vs Weak
            if effective_acc >= 75.0:
                strong.append(lm.topic)
            elif effective_acc < 55.0:
                weak.append(lm.topic)

            # Topics needing review (due next_review or low recall reliability)
            is_due = lm.next_review is not None and lm.next_review <= now
            is_low_recall = (lm.recall_reliability or 0.5) < 0.60
            if is_due or is_low_recall:
                needing_review.append({
                    "topic": lm.topic,
                    "recall_reliability": lm.recall_reliability,
                    "next_review": lm.next_review.strftime("%Y-%m-%d") if lm.next_review else "Overdue"
                })

            # Improving detection from rolling performance history
            history = lm.recent_performance_json or []
            if len(history) >= 2:
                recent_score = history[-1].get("score", 0.0)
                prev_score = history[-2].get("score", 0.0)
                diff = round(recent_score - prev_score, 1)
                if diff >= 5.0:
                    improving.append({
                        "topic": lm.topic,
                        "change": diff
                    })

        return {
            "strong": strong,
            "weak": weak,
            "improving": improving,
            "needing_review": needing_review
        }

    def calculate_progress_summary(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Generates comprehensive aggregate student progress matching frontend expectations.
        """
        # Ensure duplicate learner models are consolidated
        self.consolidate_learner_models(db, user_id)

        progress = db.query(Progress).filter(Progress.user_id == user_id).first()
        learner_models = db.query(LearnerModel).filter(LearnerModel.user_id == user_id).all()
        quiz_attempts = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.status == "completed"
        ).order_by(QuizAttempt.completed_at.asc(), QuizAttempt.id.asc()).all()
        study_sessions = db.query(StudySession).filter(StudySession.user_id == user_id).all()

        # Count total known topics from library
        materials = db.query(Material).filter(Material.user_id == user_id).all()
        library_topics = set()
        for m in materials:
            for t in (m.topics_json or []):
                t_name = t.get("name") if isinstance(t, dict) else t
                if t_name:
                    library_topics.add(self.normalize_topic_name(t_name, db))
        for lm in learner_models:
            library_topics.add(lm.topic)

        total_topics = max(len(library_topics), 7)
        completed_topics = sum(1 for lm in learner_models if lm.mastery >= 75.0)

        # Performance over time (from completed quiz attempts with compact time-aware labels)
        performance_over_time = []
        for a in quiz_attempts[-12:]:
            dt = a.completed_at or a.created_at
            d_label = dt.strftime("%b %d %H:%M") if dt else "Recent"
            performance_over_time.append({
                "date": d_label,
                "accuracy": round(a.accuracy, 1)
            })

        if not performance_over_time:
            performance_over_time = [{"date": "Today", "accuracy": round(progress.overall_accuracy, 1) if progress else 0.0}]

        # Topic-wise accuracy for BarChart and analytics
        topic_accuracy = []
        for lm in learner_models:
            topic_accuracy.append({
                "topic": lm.topic,
                "accuracy": round(lm.quiz_accuracy if lm.quiz_accuracy > 0 else lm.mastery, 1),
                "mastery": round(lm.mastery, 1),
                "recall_reliability": round(lm.recall_reliability, 2),
                "difficulty": lm.difficulty
            })

        topic_accuracy.sort(key=lambda x: x["accuracy"], reverse=True)

        # Weekly study minutes breakdown (last 7 days Mon-Sun)
        days_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        weekly_study_dict = {d: 0 for d in days_map}
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        for s in study_sessions:
            if s.start_time and s.start_time >= seven_days_ago:
                day_name = days_map[s.start_time.weekday()]
                weekly_study_dict[day_name] += s.duration_minutes

        # Also credit quiz attempts as study time (~2 min per question)
        for a in quiz_attempts:
            if a.completed_at and a.completed_at >= seven_days_ago:
                day_name = days_map[a.completed_at.weekday()]
                weekly_study_dict[day_name] += max(2, a.total_questions * 2)

        weekly_study = [{"day": d, "minutes": weekly_study_dict[d]} for d in days_map]

        # Categorize topics
        detections = self.detect_topics(learner_models)

        # Overall aggregate accuracy
        total_questions = progress.questions_attempted if progress else 0
        overall_acc = round(progress.overall_accuracy, 1) if progress else 0.0
        total_study_mins = progress.total_study_time_minutes if progress else 0
        if total_study_mins == 0:
            total_study_mins = sum(s["minutes"] for s in weekly_study)

        avg_mastery = round(sum(lm.mastery for lm in learner_models) / len(learner_models), 1) if learner_models else overall_acc
        overall_progress = int(round(min(100, max(0, avg_mastery))))

        # Flashcard performance & recall reliability
        fc_models = [lm.flashcard_performance for lm in learner_models if lm.flashcard_performance > 0]
        avg_fc = round(sum(fc_models) / len(fc_models), 1) if fc_models else 0.0
        avg_recall = round(sum(lm.recall_reliability for lm in learner_models) / len(learner_models), 2) if learner_models else 0.5
        recall_pct = int(round(avg_recall * 100))

        return {
            "stats": {
                "accuracy": int(round(overall_acc)),
                "questionsAttempted": int(total_questions),
                "studyMinutes": int(total_study_mins),
                "topicsCompleted": int(completed_topics),
                "totalTopics": int(total_topics),
                "overallProgress": int(overall_progress),
                "flashcardPerformance": int(round(avg_fc)),
                "recallReliability": int(recall_pct),
                "averageMastery": int(round(avg_mastery))
            },
            "performanceOverTime": performance_over_time,
            "topicAccuracy": topic_accuracy,
            "weeklyStudy": weekly_study,
            "recentlyImproved": detections["improving"][:3],
            "strongTopics": detections["strong"],
            "weakTopics": detections["weak"],
            "topicsNeedingReview": detections["needing_review"]
        }

learner_service = LearnerService()
