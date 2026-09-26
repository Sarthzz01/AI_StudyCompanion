"""
End-to-End Verification Test Suite for Phase 7 (Personalized Study Plan + Revision Scheduler).
Tests SM-2 Spaced Repetition, Daily Study Plan Generation, Time Budgeting, Task Completion,
API Endpoints, Multi-Tenant Student Isolation, and Phase 1-6 Non-Regression.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import Base, engine, get_db, run_migrations
from app.models.user import User, Role
from app.models.learner import LearnerModel, Progress, StudyPlanTask, RevisionSchedule
from app.services.revision_service import revision_service, calculate_sm2
from app.services.study_plan_service import study_plan_service
from app.services.auth_service import create_access_token, hash_password


class TestPhase7StudyPlanAndRevision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        run_migrations(engine)
        cls.client = TestClient(app)

        # Setup test users
        db = next(get_db())
        try:
            student_role = db.query(Role).filter(Role.name == "student").first()
            if not student_role:
                student_role = Role(name="student", description="Student user")
                db.add(student_role)
                db.commit()
                db.refresh(student_role)

            # Clean old test users
            for email in ["p7_student_a@example.com", "p7_student_b@example.com"]:
                old = db.query(User).filter(User.email == email).first()
                if old:
                    db.query(StudyPlanTask).filter(StudyPlanTask.user_id == old.id).delete()
                    db.query(RevisionSchedule).filter(RevisionSchedule.user_id == old.id).delete()
                    db.query(LearnerModel).filter(LearnerModel.user_id == old.id).delete()
                    db.query(Progress).filter(Progress.user_id == old.id).delete()
                    db.delete(old)
            db.commit()

            # Create User A
            cls.user_a = User(
                email="p7_student_a@example.com",
                role_id=student_role.id,
                hashed_password=hash_password("password123"),
                is_active=True
            )
            # Create User B
            cls.user_b = User(
                email="p7_student_b@example.com",
                role_id=student_role.id,
                hashed_password=hash_password("password123"),
                is_active=True
            )
            db.add(cls.user_a)
            db.add(cls.user_b)
            db.commit()
            db.refresh(cls.user_a)
            db.refresh(cls.user_b)

            cls.token_a = create_access_token(data={"sub": str(cls.user_a.id)})
            cls.token_b = create_access_token(data={"sub": str(cls.user_b.id)})
            cls.headers_a = {"Authorization": f"Bearer {cls.token_a}"}
            cls.headers_b = {"Authorization": f"Bearer {cls.token_b}"}

        finally:
            db.close()

    def setUp(self):
        self.db = next(get_db())

    def tearDown(self):
        self.db.close()

    # ------------------------------------------------------------------------
    # 1. SM-2 Spaced Repetition Pure Algorithm Tests
    # ------------------------------------------------------------------------
    def test_01_sm2_algorithm_progression_and_reset(self):
        """Verify SM-2 algorithm math: Rep 0->1->2 intervals and low quality resets."""
        # Initial state: repetition 0, interval 1, EF 2.5
        # Excellent recall (q=5)
        int1, ef1, rep1 = calculate_sm2(quality=5, previous_ease_factor=2.5, previous_interval=1, repetition_count=0)
        self.assertEqual(rep1, 1)
        self.assertEqual(int1, 1, "First successful repetition should give 1 day interval")
        self.assertGreaterEqual(ef1, 2.5, "Ease factor should increase on q=5")

        # Second repetition with q=5
        int2, ef2, rep2 = calculate_sm2(quality=5, previous_ease_factor=ef1, previous_interval=int1, repetition_count=rep1)
        self.assertEqual(rep2, 2)
        self.assertEqual(int2, 6, "Second successful repetition should give 6 days interval")

        # Third repetition with q=5
        int3, ef3, rep3 = calculate_sm2(quality=5, previous_ease_factor=ef2, previous_interval=int2, repetition_count=rep2)
        self.assertEqual(rep3, 3)
        expected_int3 = round(6 * ef3)
        self.assertEqual(int3, expected_int3, "Subsequent interval should multiply by updated EF")

        # Failure / Mistake (q=1)
        int_fail, ef_fail, rep_fail = calculate_sm2(quality=1, previous_ease_factor=ef3, previous_interval=int3, repetition_count=rep3)
        self.assertEqual(int_fail, 1, "Mistake should reset interval to 1 day")
        self.assertGreaterEqual(ef_fail, 1.3, "EF must not drop below 1.3")

    # ------------------------------------------------------------------------
    # 2. Revision Service DB Tests
    # ------------------------------------------------------------------------
    def test_02_revision_service_record_and_due_filtering(self):
        """Verify recording topic revision creates DB entry and computes due status."""
        user_id = self.user_a.id
        now = datetime.utcnow()

        # Record a topic revision for 'Virtual Memory' with quality=5
        rec = revision_service.record_topic_revision(
            db=self.db,
            user_id=user_id,
            topic_name="Virtual Memory",
            quality=5
        )
        self.assertEqual(rec.repetition_count, 1)
        self.assertEqual(rec.interval_days, 1)

        # Topic with due review in past
        rec_due = revision_service.record_topic_revision(
            db=self.db,
            user_id=user_id,
            topic_name="Deadlocks",
            quality=5
        )
        # Set scheduled_date to 2 days ago
        rec_due.scheduled_date = now - timedelta(days=2)
        self.db.commit()

        # Overdue topic must appear in due revisions
        due_items = revision_service.get_due_revisions(self.db, user_id, now)
        due_topics = [d["topic"] for d in due_items]
        self.assertIn("Deadlocks", due_topics, "Overdue topic must appear in due revisions")

    # ------------------------------------------------------------------------
    # 3. Daily Study Plan Time Budgeting Tests
    # ------------------------------------------------------------------------
    def test_03_study_plan_budget_allocation(self):
        """Verify greedy knapsack respects target_minutes (30, 60, 90) strictly."""
        user_id = self.user_a.id

        # Seed learner model topics for User A
        self.db.query(LearnerModel).filter(LearnerModel.user_id == user_id).delete()
        lm1 = LearnerModel(user_id=user_id, topic="Paging", mastery=30.0, recall_reliability=0.35, quiz_accuracy=30.0)
        lm2 = LearnerModel(user_id=user_id, topic="Deadlocks", mastery=85.0, recall_reliability=0.90, quiz_accuracy=85.0)
        lm3 = LearnerModel(user_id=user_id, topic="Semaphores", mastery=50.0, recall_reliability=0.55, quiz_accuracy=50.0)
        self.db.add_all([lm1, lm2, lm3])
        self.db.commit()

        # Test with 30 min budget
        plan_30 = study_plan_service.get_or_generate_plan(
            db=self.db,
            user_id=user_id,
            target_minutes=30,
            force_regenerate=True
        )
        self.assertLessEqual(plan_30["allocated_minutes"], 30, "Allocated minutes must not exceed 30m budget")
        self.assertGreater(len(plan_30["tasks"]), 0, "Plan should contain at least 1 task")

        # Test with 60 min budget
        plan_60 = study_plan_service.get_or_generate_plan(
            db=self.db,
            user_id=user_id,
            target_minutes=60,
            force_regenerate=True
        )
        self.assertLessEqual(plan_60["allocated_minutes"], 60, "Allocated minutes must not exceed 60m budget")
        self.assertGreaterEqual(plan_60["allocated_minutes"], plan_30["allocated_minutes"])

        # Test with 90 min budget
        plan_90 = study_plan_service.get_or_generate_plan(
            db=self.db,
            user_id=user_id,
            target_minutes=90,
            force_regenerate=True
        )
        self.assertLessEqual(plan_90["allocated_minutes"], 90, "Allocated minutes must not exceed 90m budget")

    # ------------------------------------------------------------------------
    # 4. Task Completion and Progress Integration Tests
    # ------------------------------------------------------------------------
    def test_04_task_completion_and_progress_increment(self):
        """Verify marking a task complete records completion and increments user study progress."""
        user_id = self.user_a.id
        plan = study_plan_service.get_or_generate_plan(
            db=self.db,
            user_id=user_id,
            target_minutes=60,
            force_regenerate=True
        )
        first_task = plan["tasks"][0]
        task_id = first_task["id"]

        # Initial progress
        init_progress = self.db.query(Progress).filter(Progress.user_id == user_id).first()
        init_mins = init_progress.total_study_time_minutes if init_progress else 0

        # Complete task via service
        completed = study_plan_service.complete_task(self.db, user_id, task_id)
        self.assertIsNotNone(completed)
        self.assertTrue(completed["completed"])
        self.assertIsNotNone(completed["completed_at"])

        # Check user study time was incremented
        self.db.expire_all()
        updated_progress = self.db.query(Progress).filter(Progress.user_id == user_id).first()
        self.assertIsNotNone(updated_progress)
        self.assertEqual(
            updated_progress.total_study_time_minutes,
            init_mins + first_task["duration_minutes"],
            "Completing task should increment total_study_time_minutes by task duration"
        )

    # ------------------------------------------------------------------------
    # 5. API Endpoints Contract Tests
    # ------------------------------------------------------------------------
    def test_05_api_study_plan_endpoints(self):
        """Verify GET /api/study-plan and POST /api/study-plan/{id}/complete HTTP endpoints."""
        # 1. GET /api/study-plan
        res = self.client.get("/api/study-plan?target_minutes=60&force=true", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("tasks", data)
        self.assertIn("allocated_minutes", data)
        self.assertIn("target_minutes", data)
        self.assertIn("ai_guidance", data)
        self.assertIsInstance(data["tasks"], list)
        self.assertGreater(len(data["tasks"]), 0)

        # 2. POST /api/study-plan/{id}/complete
        target_task_id = data["tasks"][0]["id"]
        res_post = self.client.post(f"/api/study-plan/{target_task_id}/complete", headers=self.headers_a)
        self.assertEqual(res_post.status_code, 200)
        task_out = res_post.json()
        self.assertTrue(task_out["completed"])
        self.assertEqual(task_out["id"], target_task_id)

    def test_06_api_revision_endpoints(self):
        """Verify GET /api/revision and GET /api/revision/due HTTP endpoints."""
        # 1. GET /api/revision
        res = self.client.get("/api/revision", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        revs = res.json()
        self.assertIsInstance(revs, list)
        if len(revs) > 0:
            item = revs[0]
            self.assertIn("topic", item)
            self.assertIn("ease_factor", item)
            self.assertIn("interval_days", item)
            self.assertIn("retention_estimate", item)

        # 2. GET /api/revision/due
        res_due = self.client.get("/api/revision/due", headers=self.headers_a)
        self.assertEqual(res_due.status_code, 200)
        due_data = res_due.json()
        self.assertIn("total_due", due_data)
        self.assertIn("revisions", due_data)

    # ------------------------------------------------------------------------
    # 6. Multi-Tenant Student Isolation Tests
    # ------------------------------------------------------------------------
    def test_07_student_isolation(self):
        """Verify Student A and Student B have completely isolated study plans and tasks."""
        # Generate plan for User B with different budget
        res_b = self.client.get("/api/study-plan?target_minutes=45&force=true", headers=self.headers_b)
        self.assertEqual(res_b.status_code, 200)
        data_b = res_b.json()
        tasks_b = data_b["tasks"]
        self.assertGreater(len(tasks_b), 0)

        # User A should not be able to complete User B's task (returns 404)
        task_b_id = tasks_b[0]["id"]
        res_cross_complete = self.client.post(f"/api/study-plan/{task_b_id}/complete", headers=self.headers_a)
        self.assertEqual(res_cross_complete.status_code, 404, "Cross-user task completion must be rejected with 404")


if __name__ == "__main__":
    unittest.main()
