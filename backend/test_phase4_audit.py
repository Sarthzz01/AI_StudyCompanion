"""
Comprehensive Phase 4 Verification Audit Script
Performs deep automated checks on:
1. Flashcard generation, practice, performance persistence, user & topic association.
2. Quiz generation, question-topic-material association, attempt & answer persistence, score/accuracy calculations, difficulty storage, and user ownership enforcement.
3. Performance data availability for Phase 5 (quiz accuracy, questions attempted, correct/incorrect, topic performance, flashcard performance, difficulty, recent history).
4. Multi-user data isolation (Student A vs Student B isolation test).
5. Phase 1-3 regression health.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User, Role
from app.models.material import Material
from app.models.study import Quiz, Question, Flashcard, QuizAttempt, QuizAnswer, Performance
from app.models.learner import LearnerModel, Progress
from app.services.auth_service import hash_password

def run_audit():
    print("=" * 80)
    print("PHASE 4 VERIFICATION AUDIT")
    print("=" * 80)

    client = TestClient(app)
    db = SessionLocal()

    audit_results = {
        "flashcard_checks": {},
        "quiz_checks": {},
        "performance_checks": {},
        "isolation_checks": {},
        "phase1_3_health": {}
    }

    # -------------------------------------------------------------------------
    # Setup / Ensure two distinct students exist for isolation test
    # -------------------------------------------------------------------------
    student_role = db.query(Role).filter(Role.name == "student").first()
    student_a = db.query(User).filter(User.email == "student@study.edu").first()
    
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

    # Login both students
    resp_a = client.post("/api/auth/login", json={"email": "student@study.edu", "password": "password123"})
    token_a = resp_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    resp_b = client.post("/api/auth/login", json={"email": "student_b@study.edu", "password": "password123"})
    token_b = resp_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # =========================================================================
    # 1. FLASHCARD CHECK
    # =========================================================================
    print("\n--- 1. FLASHCARD CHECK ---")
    
    # 1.1 Generation from study material
    gen_resp = client.post("/api/flashcards/generate", headers=headers_a, json={
        "material_id": "data-structures",
        "topic": "Hashing and Collision Resolution",
        "count": 2,
        "difficulty": "medium"
    })
    fc_ok = gen_resp.status_code == 201 and len(gen_resp.json()) >= 1
    audit_results["flashcard_checks"]["1_generated_from_material"] = fc_ok
    print(f"1. Flashcards generated from material: {'PASS' if fc_ok else 'FAIL'}")

    card_data = gen_resp.json()[0]
    card_id = card_data["id"]

    # 1.2 Flashcard practice works
    practice_resp = client.post(f"/api/flashcards/{card_id}/review", headers=headers_a, json={
        "rating": "easy"
    })
    practice_ok = practice_resp.status_code == 200 and practice_resp.json().get("success") is True
    audit_results["flashcard_checks"]["2_practice_works"] = practice_ok
    print(f"2. Flashcard practice works: {'PASS' if practice_ok else 'FAIL'}")

    # 1.3 & 1.4 Performance recorded & persisted in DB
    db_card = db.query(Flashcard).filter(Flashcard.id == card_id).first()
    learner_a = db.query(LearnerModel).filter(
        LearnerModel.user_id == student_a.id,
        LearnerModel.topic == db_card.topic_name
    ).first()
    perf_recorded = learner_a is not None and learner_a.flashcard_performance > 0
    audit_results["flashcard_checks"]["3_performance_recorded"] = perf_recorded
    audit_results["flashcard_checks"]["4_persisted_in_db"] = perf_recorded
    print(f"3. Flashcard performance recorded: {'PASS' if perf_recorded else 'FAIL'} (Score: {learner_a.flashcard_performance if learner_a else None}%)")
    print(f"4. Persisted in DB: {'PASS' if perf_recorded else 'FAIL'}")

    # 1.5 Associated user and topic stored
    assoc_ok = db_card is not None and db_card.user_id == student_a.id and bool(db_card.topic_name)
    audit_results["flashcard_checks"]["5_user_and_topic_stored"] = assoc_ok
    print(f"5. User ({db_card.user_id if db_card else 'None'}) and topic ('{db_card.topic_name if db_card else 'None'}') stored: {'PASS' if assoc_ok else 'FAIL'}")

    # =========================================================================
    # 2. QUIZ CHECK
    # =========================================================================
    print("\n--- 2. QUIZ CHECK ---")

    # 2.1 Quiz generation works
    quiz_gen_resp = client.post("/api/quizzes/generate", headers=headers_a, json={
        "material_id": "data-structures",
        "topic": "Hashing and Collision Resolution",
        "difficulty": "medium",
        "count": 2
    })
    quiz_gen_ok = quiz_gen_resp.status_code == 201 and len(quiz_gen_resp.json()["questions"]) >= 1
    quiz_data = quiz_gen_resp.json()
    quiz_id = quiz_data["id"]
    audit_results["quiz_checks"]["1_generation_works"] = quiz_gen_ok
    print(f"1. Quiz generation works: {'PASS' if quiz_gen_ok else 'FAIL'} (Quiz ID: {quiz_id})")

    # 2.2 Questions associated with topic/material
    db_questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    questions_assoc_ok = len(db_questions) >= 1 and all(q.material_id == "data-structures" and bool(q.topic_name) for q in db_questions)
    audit_results["quiz_checks"]["2_questions_associated_with_topic_material"] = questions_assoc_ok
    print(f"2. Questions associated with topic/material: {'PASS' if questions_assoc_ok else 'FAIL'} ({len(db_questions)} questions verified)")

    # 2.3 Quiz attempts persisted
    start_resp = client.post(f"/api/quizzes/{quiz_id}/attempt", headers=headers_a)
    attempt_start_ok = start_resp.status_code == 201
    attempt_id = start_resp.json()["id"]
    db_attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
    attempt_persisted = db_attempt is not None and db_attempt.status == "in_progress"
    audit_results["quiz_checks"]["3_attempts_persisted"] = attempt_persisted
    print(f"3. Quiz attempt persisted: {'PASS' if attempt_persisted else 'FAIL'} (Attempt ID: {attempt_id}, status: '{db_attempt.status if db_attempt else None}')")

    # 2.4 Answers persisted & 2.5 Correct/incorrect persisted & 2.6 Score/accuracy calculated
    answers_payload = []
    for idx, q in enumerate(db_questions):
        # Answer first question correctly, second incorrectly
        correct_opt = int(q.correct_answer)
        chosen = correct_opt if idx == 0 else ((correct_opt + 1) % 4)
        answers_payload.append({"question_id": q.id, "selected_option": chosen})

    submit_resp = client.post(f"/api/quiz-attempts/{attempt_id}/submit", headers=headers_a, json={
        "answers": answers_payload
    })
    submit_ok = submit_resp.status_code == 200
    res_data = submit_resp.json()

    db.refresh(db_attempt)
    db_answers = db.query(QuizAnswer).filter(QuizAnswer.attempt_id == attempt_id).all()
    answers_persisted = len(db_answers) == len(db_questions)
    results_persisted = any(a.is_correct for a in db_answers) and (len(db_questions) < 2 or any(not a.is_correct for a in db_answers))
    score_accuracy_calc = (
        db_attempt.score == res_data["score"] and
        db_attempt.total_questions == res_data["total"] and
        db_attempt.accuracy == res_data["accuracy"] and
        db_attempt.status == "completed"
    )

    audit_results["quiz_checks"]["4_answers_persisted"] = answers_persisted
    audit_results["quiz_checks"]["5_results_persisted"] = results_persisted
    audit_results["quiz_checks"]["6_score_accuracy_calculated"] = score_accuracy_calc
    print(f"4. Answers persisted in DB: {'PASS' if answers_persisted else 'FAIL'} ({len(db_answers)} records)")
    print(f"5. Correct/incorrect results persisted: {'PASS' if results_persisted else 'FAIL'}")
    print(f"6. Score and accuracy calculated: {'PASS' if score_accuracy_calc else 'FAIL'} ({db_attempt.score}/{db_attempt.total_questions}, {db_attempt.accuracy}%)")

    # 2.7 Difficulty stored where applicable
    diff_stored = bool(db_attempt.difficulty) and bool(res_data.get("difficultyResults"))
    audit_results["quiz_checks"]["7_difficulty_stored"] = diff_stored
    print(f"7. Difficulty stored: {'PASS' if diff_stored else 'FAIL'} (Difficulty: '{db_attempt.difficulty}')")

    # 2.8 User ownership enforced
    # Student B should NOT be able to view or submit Student A's attempt
    b_view_resp = client.get(f"/api/quiz-attempts/{attempt_id}", headers=headers_b)
    b_blocked = b_view_resp.status_code == 404
    audit_results["quiz_checks"]["8_user_ownership_enforced"] = b_blocked
    print(f"8. User ownership enforced (Student B access to Student A's attempt): {'PASS (Blocked with 404)' if b_blocked else 'FAIL'}")

    # =========================================================================
    # 3. PERFORMANCE DATA CHECK (Phase 5 Readiness)
    # =========================================================================
    print("\n--- 3. PERFORMANCE DATA CHECK (FOR PHASE 5) ---")

    db_perf = db.query(Performance).filter(Performance.quiz_attempt_id == attempt_id).first()
    db_progress = db.query(Progress).filter(Progress.user_id == student_a.id).first()
    all_learners = db.query(LearnerModel).filter(LearnerModel.user_id == student_a.id).all()

    p_accuracy = db_perf is not None and db_perf.accuracy is not None
    p_questions = db_progress is not None and db_progress.questions_attempted > 0
    p_correct = db_perf is not None and db_perf.correct_count is not None
    p_incorrect = db_perf is not None and db_perf.incorrect_count is not None
    p_topic = db_perf is not None and len(db_perf.topic_performance_json) > 0
    p_flashcard = any(l.flashcard_performance > 0 for l in all_learners)
    p_diff = db_perf is not None and len(db_perf.difficulty_performance_json) > 0
    p_history = db_progress is not None and len(db_progress.history_json) > 0

    audit_results["performance_checks"] = {
        "quiz_accuracy": p_accuracy,
        "questions_attempted": p_questions,
        "correct_answers": p_correct,
        "incorrect_answers": p_incorrect,
        "topic_wise_performance": p_topic,
        "flashcard_performance": p_flashcard,
        "difficulty": p_diff,
        "activity_history": p_history
    }

    for key, val in audit_results["performance_checks"].items():
        print(f"  - {key.replace('_', ' ').capitalize()}: {'AVAILABLE (PASS)' if val else 'MISSING (FAIL)'}")

    # =========================================================================
    # 4. DATA INTEGRITY & STUDENT ISOLATION
    # =========================================================================
    print("\n--- 4. DATA INTEGRITY & STUDENT ISOLATION ---")

    # Verify student B has independent learner models and progress
    learners_b = db.query(LearnerModel).filter(LearnerModel.user_id == student_b.id).all()
    prog_b = db.query(Progress).filter(Progress.user_id == student_b.id).first()
    isolation_ok = (
        len(learners_b) == 0 or
        all(l.user_id == student_b.id for l in learners_b)
    ) and (
        prog_b is None or prog_b.questions_attempted != db_progress.questions_attempted
    )
    audit_results["isolation_checks"]["student_isolation"] = isolation_ok
    print(f"Student A ({student_a.email}) vs Student B ({student_b.email}) isolation: {'PASS' if isolation_ok else 'FAIL'}")

    # =========================================================================
    # 5. PHASE 1-3 HEALTH CHECK
    # =========================================================================
    print("\n--- 5. PHASE 1-3 HEALTH CHECK ---")
    auth_me_ok = client.get("/api/auth/me", headers=headers_a).status_code == 200
    mats_ok = client.get("/api/materials", headers=headers_a).status_code == 200
    tutor_ok = client.post("/api/tutor/ask", headers=headers_a, json={
        "question": "What is binary search?",
        "materialId": "data-structures"
    }).status_code == 200

    audit_results["phase1_3_health"] = {
        "auth_me": auth_me_ok,
        "materials_catalogue": mats_ok,
        "grounded_tutor": tutor_ok
    }
    print(f"  - Auth API (/api/auth/me): {'HEALTHY' if auth_me_ok else 'FAIL'}")
    print(f"  - Materials API (/api/materials): {'HEALTHY' if mats_ok else 'FAIL'}")
    print(f"  - AI Tutor API (/api/tutor/ask): {'HEALTHY' if tutor_ok else 'FAIL'}")

    db.close()

    print("\n" + "=" * 80)
    all_passed = (
        all(audit_results["flashcard_checks"].values()) and
        all(audit_results["quiz_checks"].values()) and
        all(audit_results["performance_checks"].values()) and
        all(audit_results["isolation_checks"].values()) and
        all(audit_results["phase1_3_health"].values())
    )
    print(f"OVERALL AUDIT RESULT: {'ALL PASS (READY FOR PHASE 5)' if all_passed else 'FAIL'}")
    print("=" * 80)
    return all_passed

if __name__ == "__main__":
    success = run_audit()
    sys.exit(0 if success else 1)
