import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User, Role
from app.models.study import Question, QuizAttempt, QuizAnswer, Performance
from app.models.learner import LearnerModel, Progress
from app.services.auth_service import hash_password

def test_complete_progress_data_flow():
    print("=" * 80)
    print("VERIFYING COMPLETE PHASE 5 PROGRESS & LEARNER MODEL DATA FLOW")
    print("=" * 80)

    client = TestClient(app)
    db = SessionLocal()

    # Step 1: Login Student A
    resp_a = client.post("/api/auth/login", json={"email": "student@study.edu", "password": "password123"})
    assert resp_a.status_code == 200, "Student A login failed"
    headers_a = {"Authorization": f"Bearer {resp_a.json()['access_token']}"}
    print("[1] Student A logged in successfully.")

    # Step 2: Record Current Progress
    p0 = client.get("/api/progress", headers=headers_a).json()
    lm0 = client.get("/api/learner-model", headers=headers_a).json()
    att0 = client.get("/api/quiz-attempts", headers=headers_a).json()

    print(f"\n[2] Initial Progress Baseline:")
    print(f"    - Accuracy: {p0['stats']['accuracy']}%")
    print(f"    - Questions Attempted: {p0['stats']['questionsAttempted']}")
    print(f"    - Study Minutes: {p0['stats']['studyMinutes']}")
    print(f"    - Topics Completed: {p0['stats']['topicsCompleted']}/{p0['stats']['totalTopics']}")
    print(f"    - Performance Over Time Entries: {len(p0['performanceOverTime'])}")
    print(f"    - Quiz Attempts Recorded: {len(att0)}")

    initial_questions = p0['stats']['questionsAttempted']
    initial_study_time = p0['stats']['studyMinutes']
    initial_pot_count = len(p0['performanceOverTime'])
    initial_attempts_count = len(att0)

    # Step 3: Take and Submit Quiz 1 (Topic: Binary Search Trees, 3 questions, 100% correct)
    print(f"\n[3] Generating and taking Quiz 1 on 'Binary Search Trees' (3 questions)...")
    q1_gen = client.post("/api/quizzes/generate", headers=headers_a, json={
        "materialId": "data-structures",
        "topic": "Binary Search Trees",
        "difficulty": "medium",
        "count": 3
    }).json()

    quiz1_id = q1_gen["id"]
    att1_start = client.post(f"/api/quizzes/{quiz1_id}/attempt", headers=headers_a).json()
    att1_id = att1_start["id"]

    q1_objs = db.query(Question).filter(Question.quiz_id == quiz1_id).all()
    ans1 = [{"question_id": q.id, "selected_option": int(q.correct_answer)} for q in q1_objs]

    sub1 = client.post(f"/api/quiz-attempts/{att1_id}/submit", headers=headers_a, json={"answers": ans1}).json()
    assert sub1["score"] == 3 and sub1["total"] == 3 and sub1["accuracy"] == 100.0, "Quiz 1 submission scoring error"
    print(f"    [OK] Quiz 1 Submitted: Score {sub1['score']}/{sub1['total']} ({sub1['accuracy']}%)")

    # Step 4: Verify Progress and Learner Model after Quiz 1
    p1 = client.get("/api/progress", headers=headers_a).json()
    att1_list = client.get("/api/quiz-attempts", headers=headers_a).json()
    lm1_topic = client.get("/api/learner-model/Binary%20Search%20Trees", headers=headers_a).json()

    print(f"\n[4] Verified Progress after Quiz 1:")
    print(f"    - Questions Attempted: {p1['stats']['questionsAttempted']} (expected {initial_questions + 3})")
    print(f"    - Study Minutes: {p1['stats']['studyMinutes']} (increased by >= 6m)")
    print(f"    - Performance Over Time: {len(p1['performanceOverTime'])} entries")
    print(f"    - Learner Model Mastery: {lm1_topic['mastery']}% | Recall: {lm1_topic['recall_reliability']}")
    print(f"    - Learner Model AI signals: {len(lm1_topic['signals'])} generated")

    assert p1['stats']['questionsAttempted'] == initial_questions + 3, "Questions attempted did not increment by 3"
    assert p1['stats']['studyMinutes'] >= initial_study_time + 6, "Study time did not increment"
    assert len(att1_list) >= initial_attempts_count + 1 or len(att1_list) == 50, "Quiz attempt list not updated"
    assert att1_list[0]['accuracy'] == 100.0, "Latest attempt accuracy mismatch"
    assert lm1_topic['mastery'] >= 75.0, "Mastery should be high after 100% quiz"

    # Step 5: Take and Submit Quiz 2 (Topic: Graph Traversal, 2 questions, 50% correct)
    print(f"\n[5] Generating and taking Quiz 2 on 'Graph Algorithms and Dynamic Programming' (2 questions)...")
    q2_gen = client.post("/api/quizzes/generate", headers=headers_a, json={
        "materialId": "data-structures",
        "topic": "Graph Algorithms and Dynamic Programming",
        "difficulty": "hard",
        "count": 2
    }).json()

    quiz2_id = q2_gen["id"]
    att2_start = client.post(f"/api/quizzes/{quiz2_id}/attempt", headers=headers_a).json()
    att2_id = att2_start["id"]

    q2_objs = db.query(Question).filter(Question.quiz_id == quiz2_id).all()
    # Answer first correct, second wrong
    ans2 = [
        {"question_id": q2_objs[0].id, "selected_option": int(q2_objs[0].correct_answer)},
        {"question_id": q2_objs[1].id, "selected_option": (int(q2_objs[1].correct_answer) + 1) % 4}
    ]

    sub2 = client.post(f"/api/quiz-attempts/{att2_id}/submit", headers=headers_a, json={"answers": ans2}).json()
    assert sub2["score"] == 1 and sub2["total"] == 2 and sub2["accuracy"] == 50.0
    print(f"    [OK] Quiz 2 Submitted: Score {sub2['score']}/{sub2['total']} ({sub2['accuracy']}%)")

    # Step 6: Verify Cumulative Progress after Quiz 2
    p2 = client.get("/api/progress", headers=headers_a).json()
    att2_list = client.get("/api/quiz-attempts", headers=headers_a).json()

    print(f"\n[6] Verified Progress after Quiz 2:")
    print(f"    - Questions Attempted: {p2['stats']['questionsAttempted']} (expected {initial_questions + 5})")
    print(f"    - Accuracy: {p2['stats']['accuracy']}%")
    print(f"    - Study Minutes: {p2['stats']['studyMinutes']}")
    print(f"    - Latest Attempt in List: {att2_list[0]['topic']} ({att2_list[0]['accuracy']}%)")

    assert p2['stats']['questionsAttempted'] == initial_questions + 5, "Cumulative questions attempted mismatch"
    assert att2_list[0]['accuracy'] == 50.0, "Latest attempt in list is not Quiz 2"

    # Step 7: Verify Student Isolation (Student B)
    print(f"\n[7] Verifying Student Isolation...")
    resp_b = client.post("/api/auth/login", json={"email": "student_b@study.edu", "password": "password123"})
    headers_b = {"Authorization": f"Bearer {resp_b.json()['access_token']}"}

    p_b = client.get("/api/progress", headers=headers_b).json()
    att_b = client.get("/api/quiz-attempts", headers=headers_b).json()

    print(f"    - Student B Questions Attempted: {p_b['stats']['questionsAttempted']} (Student A has {p2['stats']['questionsAttempted']})")
    print(f"    - Student B Quiz Attempts Count: {len(att_b)}")
    assert p_b['stats']['questionsAttempted'] != p2['stats']['questionsAttempted'], "Student B shares progress with Student A!"
    print("    [OK] Student Isolation confirmed.")

    # Step 8: Verify Phase 1-4 Features Still Function
    print(f"\n[8] Verifying Phase 1-4 Endpoints...")
    mats = client.get("/api/materials", headers=headers_a)
    assert mats.status_code == 200 and len(mats.json()) > 0
    print("    [OK] GET /api/materials: 200 OK")

    fcs = client.get("/api/flashcards", headers=headers_a)
    assert fcs.status_code == 200
    print("    [OK] GET /api/flashcards: 200 OK")

    sums = client.get("/api/summaries", headers=headers_a)
    assert sums.status_code == 200
    print("    [OK] GET /api/summaries: 200 OK")

    db.close()

    print("\n" + "=" * 80)
    print("ALL PROGRESS DATA FLOW AND LEARNER MODEL TESTS PASSED (100% SUCCESS)!")
    print("=" * 80)

if __name__ == "__main__":
    test_complete_progress_data_flow()
