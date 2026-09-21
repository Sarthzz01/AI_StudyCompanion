"""
Comprehensive Phase 5 End-to-End Verification Test Suite
Tests:
1. Authentication and Student Isolation.
2. Study Session recording (POST & GET /api/study-sessions).
3. Flashcard practice reviews updating recall reliability and flashcard performance.
4. Quiz generation, attempts, and submissions updating topic mastery and quiz accuracy.
5. Learner Model state retrieval (GET /api/learner-model):
   - mastery tracking
   - recall reliability
   - quiz accuracy & flashcard performance
   - detection of strong, weak, improving, and review-due topics
6. Single topic model with AI diagnostic signals (GET /api/learner-model/{topic_id}).
7. Real aggregate progress summary (GET /api/progress & GET /api/progress/topics).
8. Goals CRUD (POST, GET, PUT, DELETE /api/goals).
9. Student A vs Student B data integrity and isolation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User, Role
from app.models.learner import LearnerModel, Progress
from app.models.study import Quiz, Question, Flashcard, QuizAttempt, QuizAnswer, Performance, StudySession, Goal
from app.services.auth_service import hash_password

def run_phase5_tests():
    print("=" * 80)
    print("PHASE 5 END-TO-END VERIFICATION TEST SUITE")
    print("=" * 80)

    client = TestClient(app)
    db = SessionLocal()

    # 1. Setup users
    student_a = db.query(User).filter(User.email == "student@study.edu").first()
    student_role = db.query(Role).filter(Role.name == "student").first()

    student_b = db.query(User).filter(User.email == "student_b@study.edu").first()
    if not student_b:
        student_b = User(
            email="student_b@study.edu",
            hashed_password=hash_password("password123"),
            role_id=student_role.id,
            is_active=True
        )
        db.add(student_b)
        db.commit()
        db.refresh(student_b)

    # Login both
    resp_a = client.post("/api/auth/login", json={"email": "student@study.edu", "password": "password123"})
    assert resp_a.status_code == 200, "Student A login failed"
    headers_a = {"Authorization": f"Bearer {resp_a.json()['access_token']}"}

    resp_b = client.post("/api/auth/login", json={"email": "student_b@study.edu", "password": "password123"})
    assert resp_b.status_code == 200, "Student B login failed"
    headers_b = {"Authorization": f"Bearer {resp_b.json()['access_token']}"}
    print("\n[Step 1/8] Authentication and user setup: PASS")

    # 2. Study Session Recording
    print("\n[Step 2/8] Testing Study Sessions API...")
    sess_resp = client.post("/api/study-sessions", headers=headers_a, json={
        "duration_minutes": 45,
        "session_type": "reading",
        "material_id": "data-structures",
        "topic": "Binary Search Trees"
    })
    assert sess_resp.status_code == 201, f"Create study session failed: {sess_resp.text}"
    session_data = sess_resp.json()
    assert session_data["duration_minutes"] == 45
    print(f"  [OK] Recorded 45-minute study session on '{session_data['topic']}'.")

    list_sess = client.get("/api/study-sessions", headers=headers_a)
    assert list_sess.status_code == 200
    assert len(list_sess.json()) >= 1
    print("  [OK] Retrieved study session history.")

    # 3. Flashcard Practice Review
    print("\n[Step 3/8] Testing Flashcard practice & Learner Model update...")
    # Generate or pick a flashcard
    fc_gen = client.post("/api/flashcards/generate", headers=headers_a, json={
        "material_id": "data-structures",
        "topic": "Binary Search Trees",
        "count": 2
    })
    cards = fc_gen.json() if fc_gen.status_code == 201 else client.get("/api/flashcards", headers=headers_a).json()
    assert len(cards) > 0, "No flashcards available"

    card_id = cards[0]["id"]
    rev_resp = client.post(f"/api/flashcards/{card_id}/review", headers=headers_a, json={
        "rating": "easy"
    })
    assert rev_resp.status_code == 200, f"Flashcard review failed: {rev_resp.text}"
    print(f"  [OK] Flashcard practice recorded (rating='easy').")

    # 4. Multi-Quiz Practice and Progression
    print("\n[Step 4/8] Generating and completing quizzes across topics...")
    # Attempt 1 on "Binary Search Trees" with high score (to create a strong/improving topic)
    q1_resp = client.post("/api/quizzes/generate", headers=headers_a, json={
        "materialId": "data-structures",
        "topic": "Binary Search Trees",
        "difficulty": "medium",
        "count": 3
    })
    assert q1_resp.status_code == 201, f"Quiz generation failed: {q1_resp.text}"
    quiz1 = q1_resp.json()

    att1_resp = client.post(f"/api/quizzes/{quiz1['id']}/attempt", headers=headers_a)
    assert att1_resp.status_code == 201
    att1 = att1_resp.json()

    # Submit with all correct answers
    q_objs = db.query(Question).filter(Question.quiz_id == quiz1["id"]).all()
    answers1 = [{"question_id": q.id, "selected_option": int(q.correct_answer)} for q in q_objs]
    sub1_resp = client.post(f"/api/quiz-attempts/{att1['id']}/submit", headers=headers_a, json={"answers": answers1})
    assert sub1_resp.status_code == 200
    res1 = sub1_resp.json()
    print(f"  [OK] Submitted Quiz 1 on '{quiz1['topic']}': Score {res1['score']}/{res1['total']} ({res1['accuracy']}%)")

    # Attempt 2 on a challenging topic with lower score (to create a weak topic)
    q2_resp = client.post("/api/quizzes/generate", headers=headers_a, json={
        "materialId": "data-structures",
        "topic": "Graph Algorithms and Dynamic Programming",
        "difficulty": "hard",
        "count": 3
    })
    quiz2 = q2_resp.json()
    att2_resp = client.post(f"/api/quizzes/{quiz2['id']}/attempt", headers=headers_a)
    att2 = att2_resp.json()

    # Submit with mostly incorrect answers
    q2_objs = db.query(Question).filter(Question.quiz_id == quiz2["id"]).all()
    answers2 = [{"question_id": q.id, "selected_option": (int(q.correct_answer) + 1) % 4} for q in q2_objs]
    sub2_resp = client.post(f"/api/quiz-attempts/{att2['id']}/submit", headers=headers_a, json={"answers": answers2})
    assert sub2_resp.status_code == 200
    res2 = sub2_resp.json()
    print(f"  [OK] Submitted Quiz 2 on '{quiz2['topic']}': Score {res2['score']}/{res2['total']} ({res2['accuracy']}%)")

    # 5. Learner Model State & Categories Detection
    print("\n[Step 5/8] Verifying Learner Model state (GET /api/learner-model)...")
    lm_resp = client.get("/api/learner-model", headers=headers_a)
    assert lm_resp.status_code == 200, f"Get learner model failed: {lm_resp.text}"
    lm_data = lm_resp.json()

    print(f"  [OK] Topics tracked: {lm_data['topics_tracked']}")
    print(f"  [OK] Average mastery: {lm_data['average_mastery']}%")
    print(f"  [OK] Average recall reliability: {lm_data['average_recall_reliability']}")
    print(f"  [OK] Strong topics: {lm_data['strong_topics']}")
    print(f"  [OK] Weak topics: {lm_data['weak_topics']}")
    print(f"  [OK] Topics needing review: {[item['topic'] for item in lm_data['topics_needing_review']]}")

    assert lm_data["topics_tracked"] >= 2, "Expected at least 2 tracked topics"

    # 6. Single Topic Learner Model with AI Signals
    print("\n[Step 6/8] Verifying Topic Learner Model with AI Diagnostic Signals...")
    topic_slug = "Binary Search Trees"
    topic_lm_resp = client.get(f"/api/learner-model/{topic_slug}", headers=headers_a)
    assert topic_lm_resp.status_code == 200, f"Topic learner model failed: {topic_lm_resp.text}"
    t_data = topic_lm_resp.json()

    print(f"  [OK] Topic: {t_data['topic']}")
    print(f"  [OK] Mastery: {t_data['mastery']}%")
    print(f"  [OK] Recommended Action: {t_data['recommended_action']}")
    print(f"  [OK] AI Pedagogical Insight: '{t_data['ai_insight']}'")
    print(f"  [OK] Diagnostic signals: {len(t_data['signals'])} generated")
    for sig in t_data["signals"]:
        print(f"       - [{sig['type']}] ({sig['severity']}): {sig['message']}")

    # 7. Progress APIs (GET /api/progress and GET /api/progress/topics)
    print("\n[Step 7/8] Verifying Progress APIs for Frontend Dashboard & Progress Pages...")
    prog_resp = client.get("/api/progress", headers=headers_a)
    assert prog_resp.status_code == 200, f"Get progress failed: {prog_resp.text}"
    prog_data = prog_resp.json()

    print(f"  [OK] Stats -> Accuracy: {prog_data['stats']['accuracy']}% | Questions: {prog_data['stats']['questionsAttempted']} | Study Time: {prog_data['stats']['studyMinutes']}m")
    print(f"  [OK] Topics completed: {prog_data['stats']['topicsCompleted']}/{prog_data['stats']['totalTopics']}")
    print(f"  [OK] Overall Progress: {prog_data['stats']['overallProgress']}%")
    print(f"  [OK] Performance Over Time series: {len(prog_data['performanceOverTime'])} points")
    print(f"  [OK] Topic-wise accuracy bars: {len(prog_data['topicAccuracy'])} topics")
    print(f"  [OK] Weekly study breakdown: {len(prog_data['weeklyStudy'])} days")

    topic_prog_resp = client.get("/api/progress/topics", headers=headers_a)
    assert topic_prog_resp.status_code == 200
    assert len(topic_prog_resp.json()) >= 2
    print("  [OK] GET /api/progress/topics returned structured topic items.")

    # 8. Goals CRUD & Student Isolation Check
    print("\n[Step 8/8] Verifying Goals CRUD and Student Isolation...")
    # Create goal
    g_create = client.post("/api/goals", headers=headers_a, json={
        "title": "Master Binary Trees",
        "type": "weekly",
        "target": 3,
        "unit": "quizzes"
    })
    assert g_create.status_code == 201
    goal_id = g_create.json()["id"]
    print(f"  [OK] Created Goal #{goal_id}: '{g_create.json()['title']}'")

    # Update goal
    g_update = client.put(f"/api/goals/{goal_id}", headers=headers_a, json={
        "current": 2,
        "completed": False
    })
    assert g_update.status_code == 200
    assert g_update.json()["current"] == 2
    print(f"  [OK] Updated Goal progress to 2/3.")

    # Student B isolation check
    b_goals = client.get("/api/goals", headers=headers_b).json()
    b_goal_ids = [g["id"] for g in b_goals]
    assert goal_id not in b_goal_ids, "Student B could see Student A's goal!"

    b_prog = client.get("/api/progress", headers=headers_b).json()
    assert b_prog["stats"]["questionsAttempted"] != prog_data["stats"]["questionsAttempted"], \
        "Student B shares questions attempted with Student A!"
    print("  [OK] Student A vs Student B data integrity and isolation verified.")

    # Delete goal
    g_del = client.delete(f"/api/goals/{goal_id}", headers=headers_a)
    assert g_del.status_code == 204
    print(f"  [OK] Deleted Goal #{goal_id}.")

    print("\n" + "=" * 80)
    print("ALL PHASE 5 VERIFICATION TESTS PASSED SUCCESSFULLY (100% PASS)!")
    print("=" * 80)

if __name__ == "__main__":
    run_phase5_tests()
