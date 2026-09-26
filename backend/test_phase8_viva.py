"""
End-to-End Verification Test Suite for Phase 8: AI Viva / Technical Viva / Interview Practice.
Tests all 3 viva modes (Basic, Technical, Interview), AI answer evaluation across 4 dimensions,
dynamic follow-up generation, final report generation, Learner Model sync, and student isolation.
"""

import os
import sys
import unittest
from datetime import datetime

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import Base, engine, get_db, run_migrations
from app.models.user import User, Role
from app.models.learner import LearnerModel, Progress
from app.models.viva import VivaSession, VivaQuestion, VivaAnswer, VivaEvaluation
from app.services.auth_service import create_access_token, hash_password
from app.services.learner_service import learner_service


class TestPhase8Viva(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        run_migrations(engine)
        cls.client = TestClient(app)

        db = next(get_db())
        try:
            student_role = db.query(Role).filter(Role.name == "student").first()
            if not student_role:
                student_role = Role(name="student", description="Student user")
                db.add(student_role)
                db.commit()
                db.refresh(student_role)

            # Clean old test users
            for email in ["p8_student_a@example.com", "p8_student_b@example.com"]:
                old = db.query(User).filter(User.email == email).first()
                if old:
                    db.query(VivaEvaluation).filter(VivaEvaluation.session_id.in_(
                        db.query(VivaSession.id).filter(VivaSession.user_id == old.id)
                    )).delete(synchronize_session=False)
                    db.query(VivaAnswer).filter(VivaAnswer.user_id == old.id).delete()
                    db.query(VivaQuestion).filter(VivaQuestion.session_id.in_(
                        db.query(VivaSession.id).filter(VivaSession.user_id == old.id)
                    )).delete(synchronize_session=False)
                    db.query(VivaSession).filter(VivaSession.user_id == old.id).delete()
                    db.query(LearnerModel).filter(LearnerModel.user_id == old.id).delete()
                    db.query(Progress).filter(Progress.user_id == old.id).delete()
                    db.delete(old)
            db.commit()

            # Create User A
            cls.user_a = User(
                email="p8_student_a@example.com",
                role_id=student_role.id,
                hashed_password=hash_password("password123"),
                is_active=True
            )
            # Create User B
            cls.user_b = User(
                email="p8_student_b@example.com",
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
    # 1. Mode 1: Basic Viva Flow
    # ------------------------------------------------------------------------
    def test_01_basic_viva_start_and_evaluate(self):
        """Test starting a Basic Viva on Deadlocks, submitting an answer, and receiving evaluation."""
        payload = {
            "topic": "Deadlocks",
            "mode": "basic",
            "difficulty": "medium",
            "material_id": "operating-systems",
            "total_questions": 3
        }
        res = self.client.post("/api/viva/start", json=payload, headers=self.headers_a)
        self.assertEqual(res.status_code, 201, f"Expected 201 Created: {res.text}")
        data = res.json()
        
        session_id = data["session_id"]
        q1 = data["current_question"]
        self.assertEqual(data["mode"], "basic")
        self.assertEqual(data["topic"], "Deadlocks")
        self.assertIn("id", q1)
        self.assertGreater(len(q1["question_text"]), 10)

        # Submit answer to Question 1
        answer_payload = {
            "question_id": q1["id"],
            "answer_text": (
                "A deadlock occurs when two or more processes are blocked waiting for resources held by each other, "
                "such that none can proceed. The four necessary conditions are Mutual Exclusion, Hold and Wait, "
                "No Preemption, and Circular Wait."
            )
        }
        ans_res = self.client.post(f"/api/viva/{session_id}/answer", json=answer_payload, headers=self.headers_a)
        self.assertEqual(ans_res.status_code, 200, f"Expected 200 OK: {ans_res.text}")
        ans_data = ans_res.json()

        # Check 4-dimension evaluation metrics
        ev = ans_data["evaluation"]
        self.assertIn("correctness", ev)
        self.assertIn("relevance", ev)
        self.assertIn("completeness", ev)
        self.assertIn("conceptual_understanding", ev)
        self.assertIn("score", ev)
        self.assertGreaterEqual(ev["score"], 50.0, "Substantive answer should score >= 50%")
        self.assertGreater(len(ev["feedback"]), 10)

    # ------------------------------------------------------------------------
    # 2. Mode 2: Technical Viva Flow with Follow-Up Probe
    # ------------------------------------------------------------------------
    def test_02_technical_viva_adaptive_follow_up(self):
        """Test starting a Technical Viva on Routing Algorithms and evaluating technical depth."""
        payload = {
            "topic": "Routing Algorithms",
            "mode": "technical",
            "difficulty": "hard",
            "material_id": "computer-networks",
            "total_questions": 3
        }
        res = self.client.post("/api/viva/start", json=payload, headers=self.headers_a)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        session_id = data["session_id"]
        q1 = data["current_question"]

        # Submit brief answer to trigger adaptive follow-up
        ans_res = self.client.post(
            f"/api/viva/{session_id}/answer",
            json={
                "question_id": q1["id"],
                "answer_text": "Link state uses Dijkstra's algorithm to compute shortest path tree from link states."
            },
            headers=self.headers_a
        )
        self.assertEqual(ans_res.status_code, 200)
        ans_data = ans_res.json()
        self.assertTrue(ans_data["has_next_question"])
        self.assertIsNotNone(ans_data["next_question"])

    # ------------------------------------------------------------------------
    # 3. Mode 3: Technical Interview Scenario Flow & Final Report
    # ------------------------------------------------------------------------
    def test_03_interview_mode_full_lifecycle_and_report(self):
        """Test full Interview lifecycle from start through Q&A to End Report and LearnerModel update."""
        payload = {
            "topic": "Graph Traversal",
            "mode": "interview",
            "difficulty": "medium",
            "material_id": "data-structures",
            "total_questions": 2
        }
        start_res = self.client.post("/api/viva/start", json=payload, headers=self.headers_a)
        self.assertEqual(start_res.status_code, 201)
        session_id = start_res.json()["session_id"]
        q1 = start_res.json()["current_question"]

        # Answer Q1
        ans1_res = self.client.post(
            f"/api/viva/{session_id}/answer",
            json={
                "question_id": q1["id"],
                "answer_text": (
                    "In a production system with cycle detection in dependency graphs, I would implement Tarjan's "
                    "or Kahn's topological sort using BFS with indegrees. Kahn's uses a queue for zero in-degree nodes, "
                    "giving O(V+E) time complexity and O(V) space."
                )
            },
            headers=self.headers_a
        )
        self.assertEqual(ans1_res.status_code, 200)
        q2 = ans1_res.json()["next_question"]

        # Answer Q2
        ans2_res = self.client.post(
            f"/api/viva/{session_id}/answer",
            json={
                "question_id": q2["id"],
                "answer_text": (
                    "For large-scale distributed graphs exceeding single-node RAM, I would use Pregel or GraphX "
                    "with vertex-centric message passing, partitioning vertices via hash or min-cut algorithms."
                )
            },
            headers=self.headers_a
        )
        self.assertEqual(ans2_res.status_code, 200)

        # End Session & Generate Report
        end_res = self.client.post(f"/api/viva/{session_id}/end", headers=self.headers_a)
        self.assertEqual(end_res.status_code, 200)
        report = end_res.json()

        self.assertEqual(report["status"], "completed")
        self.assertGreater(report["overall_score"], 0.0)
        self.assertGreater(report["correctness_score"], 0.0)
        self.assertGreater(report["conceptual_score"], 0.0)
        self.assertGreaterEqual(len(report["strengths"]), 1)
        self.assertGreaterEqual(len(report["suggested_improvements"]), 1)
        self.assertEqual(len(report["transcript"]), 2)

    # ------------------------------------------------------------------------
    # 4. Learner Model & Spaced Repetition Integration
    # ------------------------------------------------------------------------
    def test_04_viva_updates_learner_model(self):
        """Verify that completing a viva session updates viva_performance and composite mastery in LearnerModel."""
        lm = self.db.query(LearnerModel).filter(
            LearnerModel.user_id == self.user_a.id,
            LearnerModel.topic == "Graph Traversal"
        ).first()
        self.assertIsNotNone(lm, "LearnerModel record for Graph Traversal should be created/updated by viva")
        self.assertGreater(lm.viva_performance, 0.0, "viva_performance must be updated")
        self.assertGreater(lm.mastery, 0.0, "composite mastery must be updated")
        self.assertIsNotNone(lm.last_reviewed, "last_reviewed must be updated")

        # Verify history JSON includes viva entry
        history_types = [h.get("type") for h in (lm.recent_performance_json or [])]
        self.assertIn("viva", history_types, "LearnerModel history must log viva event")

    # ------------------------------------------------------------------------
    # 5. History and Detail Endpoints
    # ------------------------------------------------------------------------
    def test_05_get_history_and_session_detail(self):
        """Verify GET /api/viva/history and GET /api/viva/{session_id} APIs."""
        hist_res = self.client.get("/api/viva/history", headers=self.headers_a)
        self.assertEqual(hist_res.status_code, 200)
        hist_data = hist_res.json()
        self.assertGreaterEqual(hist_data["total_sessions"], 2)
        self.assertGreater(hist_data["average_score"], 0.0)

        latest_id = hist_data["sessions"][0]["id"]
        detail_res = self.client.get(f"/api/viva/{latest_id}", headers=self.headers_a)
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        self.assertEqual(detail["id"], latest_id)
        self.assertIn("transcript", detail)

    # ------------------------------------------------------------------------
    # 6. Multi-Tenant Student Isolation
    # ------------------------------------------------------------------------
    def test_06_student_isolation(self):
        """Verify Student B cannot access Student A's viva sessions."""
        # Get Student A's session ID
        hist_a = self.client.get("/api/viva/history", headers=self.headers_a).json()
        session_a_id = hist_a["sessions"][0]["id"]

        # Student B attempts to access Student A's session
        res = self.client.get(f"/api/viva/{session_a_id}", headers=self.headers_b)
        self.assertEqual(res.status_code, 404, "Student B should not have access to Student A's viva session")

        # Student B's history should be empty initially
        hist_b = self.client.get("/api/viva/history", headers=self.headers_b).json()
        self.assertEqual(hist_b["total_sessions"], 0)


if __name__ == "__main__":
    unittest.main()
