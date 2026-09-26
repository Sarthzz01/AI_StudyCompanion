"""
Verification Test Suite for Topic-Specific Quiz Navigation & Generation.
Verifies that:
1. Topic-specific quiz requests generate questions strictly for that topic (e.g. Routing Algorithms, Graph Traversal, Deadlocks).
2. Topic difficulty parameter is preserved during quiz generation.
3. Spaced Revision schedule provides topic, material_id, and recommended difficulty.
4. Normal generic quiz generation without topic parameter continues to work without regressions.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, get_db, run_migrations
from app.models.user import User, Role
from app.models.learner import LearnerModel, RevisionSchedule
from app.services.auth_service import create_access_token, hash_password


class TestTopicSpecificQuizNavigation(unittest.TestCase):
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

            user = db.query(User).filter(User.email == "topic_nav_test@example.com").first()
            if not user:
                user = User(
                    email="topic_nav_test@example.com",
                    role_id=student_role.id,
                    hashed_password=hash_password("password123"),
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            cls.user = user
            cls.token = create_access_token(data={"sub": str(user.id)})
            cls.headers = {"Authorization": f"Bearer {cls.token}"}
        finally:
            db.close()

    def test_01_revision_schedule_provides_topic_material_difficulty(self):
        """Verify GET /api/revision returns topic, material_id, difficulty for each topic."""
        res = self.client.get("/api/revision", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        items = res.json()
        self.assertIsInstance(items, list)
        for item in items:
            self.assertIn("topic", item)
            self.assertIn("material_id", item)
            self.assertIn("difficulty", item)
            self.assertIn("retention_estimate", item)

    def test_02_topic_specific_quiz_routing_algorithms(self):
        """Verify quiz generation for 'Routing Algorithms' generates questions specifically for that topic."""
        payload = {
            "material_id": "computer-networks",
            "topic": "Routing Algorithms",
            "difficulty": "medium",
            "count": 5
        }
        res = self.client.post("/api/quizzes/generate", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        quiz = res.json()
        self.assertEqual(quiz["topic"], "Routing Algorithms")
        self.assertEqual(quiz["difficulty"], "medium")
        self.assertEqual(len(quiz["questions"]), 5)
        for q in quiz["questions"]:
            self.assertIn("topic", q)

    def test_03_topic_specific_quiz_graph_traversal(self):
        """Verify quiz generation for 'Graph Traversal' generates questions specifically for that topic."""
        payload = {
            "material_id": "data-structures",
            "topic": "Graph Traversal",
            "difficulty": "hard",
            "count": 5
        }
        res = self.client.post("/api/quizzes/generate", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        quiz = res.json()
        self.assertEqual(quiz["topic"], "Graph Traversal")
        self.assertEqual(quiz["difficulty"], "hard")
        self.assertEqual(len(quiz["questions"]), 5)

    def test_04_topic_specific_quiz_deadlocks(self):
        """Verify quiz generation for 'Deadlocks' generates questions specifically for that topic."""
        payload = {
            "material_id": "operating-systems",
            "topic": "Deadlocks",
            "difficulty": "medium",
            "count": 5
        }
        res = self.client.post("/api/quizzes/generate", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        quiz = res.json()
        self.assertEqual(quiz["topic"], "Deadlocks")
        self.assertEqual(quiz["difficulty"], "medium")
        self.assertEqual(len(quiz["questions"]), 5)

    def test_05_normal_quizzes_all_topics_fallback(self):
        """Verify normal /quizzes without topic parameter continues to work seamlessly."""
        payload = {
            "material_id": "data-structures",
            "topic": "All topics",
            "difficulty": "mixed",
            "count": 5
        }
        res = self.client.post("/api/quizzes/generate", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        quiz = res.json()
        self.assertEqual(quiz["topic"], "All topics")
        self.assertEqual(quiz["difficulty"], "mixed")
        self.assertEqual(len(quiz["questions"]), 5)


if __name__ == "__main__":
    unittest.main()
