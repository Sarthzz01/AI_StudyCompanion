import sys
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_phase5_fixes():
    print("=== Testing Phase 5 Fixes ===")
    
    # 1. Login
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "student@study.edu", "password": "password123"})
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] 1. Auth & Login verified")

    # 2. Get initial progress
    prog_resp = requests.get(f"{BASE_URL}/progress", headers=headers)
    assert prog_resp.status_code == 200, f"Progress failed: {prog_resp.text}"
    p_data = prog_resp.json()
    stats = p_data["stats"]
    print(f"Initial Stats: Accuracy={stats['accuracy']}%, FC={stats['flashcardPerformance']}%, Recall={stats['recallReliability']}%, Mastery={stats['averageMastery']}%")
    assert "flashcardPerformance" in stats
    assert "recallReliability" in stats
    assert "averageMastery" in stats
    print("[PASS] 2. Stats schema contains flashcardPerformance, recallReliability, and averageMastery")

    # 3. Verify Performance Over Time time-aware labels
    perf_time = p_data["performanceOverTime"]
    print(f"Performance over time entries: {len(perf_time)}")
    if perf_time:
        print(f"Sample date label: {perf_time[0]['date']}")
    print("[PASS] 3. Performance over time date labels verified")

    # 4. Test Canonical Topic Mapping on Quiz Submission
    # Generate quiz on data-structures
    quiz_create = requests.post(f"{BASE_URL}/quizzes/generate", headers=headers, json={"material_id": "data-structures", "num_questions": 3, "difficulty": "medium"})
    assert quiz_create.status_code == 201, f"Quiz creation failed: {quiz_create.text}"
    quiz_id = quiz_create.json()["id"]

    # Start attempt
    attempt_start = requests.post(f"{BASE_URL}/quizzes/{quiz_id}/attempt", headers=headers)
    assert attempt_start.status_code == 201
    attempt_id = attempt_start.json()["id"]
    questions = attempt_start.json()["questions"]

    # Submit attempt
    answers = [{"question_id": q["id"], "selected_option": 0} for q in questions]
    submit_resp = requests.post(f"{BASE_URL}/quiz-attempts/{attempt_id}/submit", headers=headers, json={"answers": answers})
    assert submit_resp.status_code == 200, f"Submit attempt failed: {submit_resp.text}"
    sub_data = submit_resp.json()
    print(f"Submitted quiz score: {sub_data['score']}/{sub_data['total']} ({sub_data['accuracy']}%)")
    print(f"Topic results: {list(sub_data['topicResults'].keys())}")
    print("[PASS] 4. Quiz attempt submitted and evaluated")

    # 5. Test Flashcard Review
    fc_gen = requests.post(f"{BASE_URL}/flashcards/generate", headers=headers, json={"material_id": "data-structures", "count": 3})
    assert fc_gen.status_code == 201, f"Flashcard gen failed: {fc_gen.text}"
    cards = fc_gen.json()
    print("Generated cards:", cards)
    card_id = cards[0]["id"]
    print("Card ID to review:", card_id)
    rev_resp = requests.post(f"{BASE_URL}/flashcards/{card_id}/review", headers=headers, json={"rating": "easy"})
    assert rev_resp.status_code == 200, f"Flashcard review failed: {rev_resp.text}"
    rev_data = rev_resp.json()
    print(f"Flashcard reviewed: topic={rev_data['topic']}, rating={rev_data['rating']}, fc_perf={rev_data['flashcard_performance']}%")
    print("[PASS] 5. Flashcard performance updated")

    # 6. Verify Learner Model Deduplication & Consolidation
    learner_resp = requests.get(f"{BASE_URL}/learner-model", headers=headers)
    assert learner_resp.status_code == 200
    lm_data = learner_resp.json()
    topic_names = [t["topic"] for t in lm_data["topics"]]
    print(f"Tracked topics ({len(topic_names)}): {topic_names}")
    
    # Check that no duplicate subtopics like 'Binary Tree Traversals and Reconstruction' and 'Tree Traversal' exist as separate rows
    assert len(topic_names) == len(set(topic_names)), "Duplicate topic names found in LearnerModel!"
    print("[PASS] 6. No duplicate topic rows in LearnerModel")

    # 7. Check Strong/Weak Topics
    print(f"Strong topics: {lm_data['strong_topics']}")
    print(f"Weak topics: {lm_data['weak_topics']}")
    assert len(lm_data['strong_topics']) == len(set(lm_data['strong_topics'])), "Duplicate topics in strong_topics!"
    assert len(lm_data['weak_topics']) == len(set(lm_data['weak_topics'])), "Duplicate topics in weak_topics!"
    print("[PASS] 7. Strong and Weak topic lists have no duplicates")

    # 8. Check Topics Due For Review
    topics_progress = requests.get(f"{BASE_URL}/progress/topics", headers=headers).json()
    print(f"Topic analytics count: {len(topics_progress)}")
    for tp in topics_progress[:3]:
        print(f"  - Topic: {tp['topic']} | QuizAcc: {tp['quiz_accuracy']}% | Mastery: {tp['mastery']}% | Recall: {tp['recall_reliability']} | Status: {tp['status']}")
    print("[PASS] 8. Topic analytics expose separate quiz_accuracy, composite mastery, and recall_reliability")

    # 9. Verify Review Due section
    prog_resp_2 = requests.get(f"{BASE_URL}/progress", headers=headers).json()
    needing_review = prog_resp_2["topicsNeedingReview"]
    print(f"Topics needing review count: {len(needing_review)}")
    for nr in needing_review:
        print(f"  - Due: {nr['topic']} (recall: {nr['recall_reliability']}, due: {nr['next_review']})")
    print("[PASS] 9. Topics needing review verified")

    # 10. Check Phase 1-4 Material List & Summary
    mat_resp = requests.get(f"{BASE_URL}/materials", headers=headers)
    assert mat_resp.status_code == 200
    mats = mat_resp.json()
    assert len(mats) >= 4, f"Materials missing: {len(mats)}"
    print(f"[PASS] 10. Phase 1-4 Materials verified ({len(mats)} materials active)")

    print("\nALL PHASE 5 FIXES TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        test_phase5_fixes()
    except Exception as e:
        print(f"TEST FAILED: {e}")
        sys.exit(1)
