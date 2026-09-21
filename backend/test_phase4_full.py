"""
Comprehensive Phase 4 Automated Verification Test Suite
Tests:
1. Student authentication (JWT acquisition)
2. Study material availability (data-structures)
3. AI Flashcard generation via POST /api/flashcards/generate
4. Flashcard retrieval via GET /api/flashcards and GET /api/flashcards/{id}
5. Flashcard practice rating & performance recording via POST /api/flashcards/{id}/review
6. AI Quiz question generation with topic & difficulty via POST /api/quizzes/generate
7. Quiz retrieval via GET /api/quizzes and GET /api/quizzes/{id}
8. Starting a quiz attempt via POST /api/quizzes/{id}/attempt
9. Submitting and evaluating a quiz attempt via POST /api/quiz-attempts/{id}/submit
10. Verifying calculated evaluation metrics: accuracy, correct/incorrect count, topic & difficulty breakdown
11. Verifying database relational storage: Flashcards, Questions, Quiz, QuizAttempt, QuizAnswer, Performance, LearnerModel, Progress
12. Historical quiz attempts listing via GET /api/quiz-attempts
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.material import Material
from app.models.study import Quiz, Question, Flashcard, QuizAttempt, QuizAnswer, Performance
from app.models.learner import LearnerModel, Progress

def run_phase4_tests():
    print("=" * 70)
    print("PHASE 4 FULL END-TO-END VERIFICATION TEST SUITE")
    print("=" * 70)

    client = TestClient(app)

    # -------------------------------------------------------------------------
    # Step 1: Authentication
    # -------------------------------------------------------------------------
    print("\n[Step 1/12] Logging in as student@study.edu...")
    auth_resp = client.post("/api/auth/login", json={
        "email": "student@study.edu",
        "password": "password123"
    })
    assert auth_resp.status_code == 200, f"Auth failed: {auth_resp.text}"
    token = auth_resp.json().get("access_token")
    assert token, "No access token received"
    headers = {"Authorization": f"Bearer {token}"}
    print("  [OK] Student authenticated successfully.")

    # -------------------------------------------------------------------------
    # Step 2: Verify Material Exists
    # -------------------------------------------------------------------------
    print("\n[Step 2/12] Verifying study material exists...")
    mat_resp = client.get("/api/materials/data-structures", headers=headers)
    assert mat_resp.status_code == 200, f"Material fetch failed: {mat_resp.text}"
    material_title = mat_resp.json().get("title")
    print(f"  [OK] Study material found: '{material_title}'")

    # -------------------------------------------------------------------------
    # Step 3: Flashcard Generation
    # -------------------------------------------------------------------------
    print("\n[Step 3/12] Testing Flashcard generation via POST /api/flashcards/generate...")
    fc_gen_resp = client.post("/api/flashcards/generate", headers=headers, json={
        "material_id": "data-structures",
        "topic": "Graph Representations and Breadth-First Search (BFS)",
        "count": 3,
        "difficulty": "medium"
    })
    assert fc_gen_resp.status_code == 201, f"Flashcard generation failed: {fc_gen_resp.text}"
    generated_cards = fc_gen_resp.json()
    assert len(generated_cards) >= 1, "Expected at least 1 generated card"
    first_card = generated_cards[0]
    assert "front" in first_card and first_card["front"], "Card front missing"
    assert "back" in first_card and first_card["back"], "Card back missing"
    assert "difficulty" in first_card, "Card difficulty missing"
    print(f"  [OK] Generated {len(generated_cards)} flashcards.")
    print(f"  [OK] Sample Front: {first_card['front'][:70]}...")
    print(f"  [OK] Sample Back:  {first_card['back'][:70]}...")

    # -------------------------------------------------------------------------
    # Step 4: Flashcard Retrieval
    # -------------------------------------------------------------------------
    print("\n[Step 4/12] Testing GET /api/flashcards and GET /api/flashcards/{id}...")
    fc_list_resp = client.get("/api/flashcards?material_id=data-structures", headers=headers)
    assert fc_list_resp.status_code == 200, f"Flashcards listing failed: {fc_list_resp.text}"
    cards_list = fc_list_resp.json()
    assert len(cards_list) > 0, "No flashcards returned from listing"

    single_card_id = first_card["id"]
    fc_single_resp = client.get(f"/api/flashcards/{single_card_id}", headers=headers)
    assert fc_single_resp.status_code == 200, f"Get single flashcard failed: {fc_single_resp.text}"
    assert fc_single_resp.json()["id"] == single_card_id
    print(f"  [OK] Retrieved {len(cards_list)} flashcards via GET /api/flashcards.")
    print(f"  [OK] Retrieved single flashcard #{single_card_id} via GET /api/flashcards/{single_card_id}.")

    # -------------------------------------------------------------------------
    # Step 5: Flashcard Practice & Performance Recording
    # -------------------------------------------------------------------------
    print("\n[Step 5/12] Testing Flashcard practice review rating via POST /api/flashcards/{id}/review...")
    review_resp = client.post(f"/api/flashcards/{single_card_id}/review", headers=headers, json={
        "rating": "easy"
    })
    assert review_resp.status_code == 200, f"Review rating failed: {review_resp.text}"
    review_data = review_resp.json()
    assert review_data.get("success") is True
    assert review_data.get("rating") == "easy"
    print(f"  [OK] Flashcard practice recorded: rating='{review_data['rating']}', topic='{review_data['topic']}'.")

    # -------------------------------------------------------------------------
    # Step 6: Quiz Generation (Difficulty-aware)
    # -------------------------------------------------------------------------
    print("\n[Step 6/12] Testing AI Quiz generation via POST /api/quizzes/generate...")
    quiz_gen_resp = client.post("/api/quizzes/generate", headers=headers, json={
        "material_id": "data-structures",
        "topic": "Graph Representations and Breadth-First Search (BFS)",
        "difficulty": "medium",
        "count": 3
    })
    assert quiz_gen_resp.status_code == 201, f"Quiz generation failed: {quiz_gen_resp.text}"
    quiz_data = quiz_gen_resp.json()
    quiz_id = quiz_data["id"]
    questions = quiz_data["questions"]
    assert len(questions) >= 1, "Expected questions in generated quiz"
    for q in questions:
        assert len(q["options"]) == 4, f"Expected 4 options in MCQ, got {len(q['options'])}"
        assert q["question"], "Question text missing"
    print(f"  [OK] Created Quiz ID {quiz_id} with {len(questions)} difficulty-aware questions.")
    print(f"  [OK] Question 1: '{questions[0]['question'][:80]}...'")
    print(f"  [OK] Options: {questions[0]['options']}")

    # -------------------------------------------------------------------------
    # Step 7: Quiz Retrieval
    # -------------------------------------------------------------------------
    print("\n[Step 7/12] Testing GET /api/quizzes and GET /api/quizzes/{id}...")
    quizzes_resp = client.get("/api/quizzes", headers=headers)
    assert quizzes_resp.status_code == 200
    assert any(q["id"] == quiz_id for q in quizzes_resp.json())

    quiz_by_id_resp = client.get(f"/api/quizzes/{quiz_id}", headers=headers)
    assert quiz_by_id_resp.status_code == 200
    assert quiz_by_id_resp.json()["id"] == quiz_id
    print(f"  [OK] Quiz verified in catalogue and retrieved by ID.")

    # -------------------------------------------------------------------------
    # Step 8: Starting a Quiz Attempt
    # -------------------------------------------------------------------------
    print("\n[Step 8/12] Starting Quiz Attempt via POST /api/quizzes/{id}/attempt...")
    attempt_resp = client.post(f"/api/quizzes/{quiz_id}/attempt", headers=headers)
    assert attempt_resp.status_code == 201, f"Starting attempt failed: {attempt_resp.text}"
    attempt_data = attempt_resp.json()
    attempt_id = attempt_data["id"]
    assert attempt_data["status"] == "in_progress"
    assert len(attempt_data["questions"]) == len(questions)
    print(f"  [OK] Active Quiz Attempt created: ID {attempt_id}, status='in_progress'.")

    # -------------------------------------------------------------------------
    # Step 9: Submitting the Quiz Attempt
    # -------------------------------------------------------------------------
    print("\n[Step 9/12] Submitting Quiz Attempt via POST /api/quiz-attempts/{id}/submit...")
    # Answer question 1 correctly (find correct option from DB), question 2 intentionally differently
    db = SessionLocal()
    db_questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    q_ans_map = {q.id: int(q.correct_answer) for q in db_questions}
    db.close()

    submission_answers = []
    for idx, q in enumerate(questions):
        correct_idx = q_ans_map.get(q["id"], 0)
        # Choose correct answer for first question, and another for subsequent to test mixed scores
        chosen_opt = correct_idx if idx == 0 else ((correct_idx + 1) % 4)
        submission_answers.append({
            "question_id": q["id"],
            "selected_option": chosen_opt
        })

    submit_resp = client.post(f"/api/quiz-attempts/{attempt_id}/submit", headers=headers, json={
        "answers": submission_answers
    })
    assert submit_resp.status_code == 200, f"Quiz submission failed: {submit_resp.text}"
    eval_result = submit_resp.json()
    print(f"  [OK] Quiz submitted and evaluated successfully.")

    # -------------------------------------------------------------------------
    # Step 10: Verify Calculated Evaluation Metrics
    # -------------------------------------------------------------------------
    print("\n[Step 10/12] Verifying calculated metrics & evaluation breakdown...")
    assert "score" in eval_result
    assert "total" in eval_result
    assert "accuracy" in eval_result
    assert "topicResults" in eval_result
    assert "difficultyResults" in eval_result
    assert "review" in eval_result
    assert len(eval_result["review"]) == len(questions)

    print(f"  [OK] Score: {eval_result['score']}/{eval_result['total']} ({eval_result['accuracy']}%)")
    print(f"  [OK] Topic Results: {eval_result['topicResults']}")
    print(f"  [OK] Difficulty Results: {eval_result['difficultyResults']}")
    print(f"  [OK] Strong Topics: {eval_result['strongTopics']}")
    print(f"  [OK] Weak Topics:   {eval_result['weakTopics']}")
    print(f"  [OK] First Review Item:")
    r0 = eval_result["review"][0]
    print(f"       Question: {r0['question'][:60]}...")
    print(f"       Selected: {r0['selected']}, Correct: {r0['answer']}, IsCorrect: {r0['correct']}")
    print(f"       Explanation: {r0['explanation'][:70]}...")

    # -------------------------------------------------------------------------
    # Step 11: Database Relational Integrity
    # -------------------------------------------------------------------------
    print("\n[Step 11/12] Verifying database records for Phase 4 models...")
    db = SessionLocal()
    try:
        # Check Quiz
        q_record = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        assert q_record is not None, "Quiz not found in DB"

        # Check Questions
        q_count = db.query(Question).filter(Question.quiz_id == quiz_id).count()
        assert q_count == len(questions), "Questions count mismatch in DB"

        # Check QuizAttempt
        qa_record = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        assert qa_record is not None, "QuizAttempt not found in DB"
        assert qa_record.status == "completed", f"Expected completed status, got {qa_record.status}"

        # Check QuizAnswers
        answers_count = db.query(QuizAnswer).filter(QuizAnswer.attempt_id == attempt_id).count()
        assert answers_count == len(questions), "QuizAnswer records count mismatch in DB"

        # Check Performance
        perf = db.query(Performance).filter(Performance.quiz_attempt_id == attempt_id).first()
        assert perf is not None, "Performance record missing in DB"
        assert perf.accuracy == eval_result["accuracy"]
        assert perf.correct_count == eval_result["score"]

        # Check LearnerModel
        student_user = db.query(User).filter(User.email == "student@study.edu").first()
        learners = db.query(LearnerModel).filter(LearnerModel.user_id == student_user.id).all()
        assert len(learners) > 0, "No LearnerModel records found for student"

        # Check Progress
        progress = db.query(Progress).filter(Progress.user_id == student_user.id).first()
        assert progress is not None, "Progress record missing for student"
        assert progress.questions_attempted >= len(questions)

        print(f"  [OK] Flashcards stored: {db.query(Flashcard).count()} total")
        print(f"  [OK] Quizzes stored: {db.query(Quiz).count()} total")
        print(f"  [OK] Questions stored: {db.query(Question).count()} total")
        print(f"  [OK] QuizAttempts stored: {db.query(QuizAttempt).count()} total")
        print(f"  [OK] QuizAnswers stored: {answers_count} linked to attempt #{attempt_id}")
        print(f"  [OK] Performance stored: accuracy={perf.accuracy}%, correct={perf.correct_count}, incorrect={perf.incorrect_count}")
        print(f"  [OK] LearnerModel prepared: {len(learners)} topic models tracked")
        print(f"  [OK] Progress recorded: {progress.questions_attempted} questions attempted across {progress.quizzes_completed} quizzes")
    finally:
        db.close()

    # -------------------------------------------------------------------------
    # Step 12: Historical Quiz Attempts Listing
    # -------------------------------------------------------------------------
    print("\n[Step 12/12] Testing GET /api/quiz-attempts (history list)...")
    history_resp = client.get("/api/quiz-attempts", headers=headers)
    assert history_resp.status_code == 200, f"History listing failed: {history_resp.text}"
    history_items = history_resp.json()
    assert any(str(item["id"]) == str(attempt_id) for item in history_items), "New attempt missing from history list"
    print(f"  [OK] Historical attempts listed ({len(history_items)} completed attempts found).")

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL PHASE 4 END-TO-END VERIFICATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_phase4_tests()
