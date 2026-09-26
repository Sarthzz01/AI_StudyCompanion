from datetime import datetime
from fastapi.testclient import TestClient
import app.models
from app.database import SessionLocal, engine, Base
from app.main import app as fastapi_app
from app.models.user import User
from app.models.study import Note, Quiz, QuizAttempt, QuizAnswer, Performance

Base.metadata.create_all(bind=engine)
client = TestClient(fastapi_app)

def run_test():
    print("=================================================================")
    print("   AI STUDY COMPANION - FULL END-TO-END FLOW VERIFICATION TEST   ")
    print("=================================================================\n")

    # 1. New Student Sign Up
    ts = int(datetime.utcnow().timestamp())
    test_email = f"student_{ts}@study.edu"
    test_password = "securePassword123"

    print(f"[Step 1/13] Registering new student: {test_email}...")
    r_signup = client.post("/api/auth/register", json={
        "name": f"Alex Student {ts}",
        "email": test_email,
        "password": test_password
    })
    assert r_signup.status_code in (200, 201), f"Signup failed: {r_signup.text}"
    print(f"  [PASS] Sign up succeeded: {r_signup.json()['user']['name']}")

    # 2. Login
    print(f"\n[Step 2/13] Logging in as new student...")
    r_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    token = r_login.json()["access_token"]
    student_id = r_login.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  [PASS] Login succeeded, access token obtained. (Student ID: {student_id})")

    # 3. Student Dashboard Access & Materials
    print(f"\n[Step 3/13] Accessing student dashboard & library materials...")
    r_mat = client.get("/api/materials", headers=headers)
    assert r_mat.status_code == 200, f"Materials fetch failed: {r_mat.text}"
    materials = r_mat.json()
    assert len(materials) > 0, "Expected available materials"
    mat_id = materials[0]["id"]
    print(f"  [PASS] Retrieved {len(materials)} study materials in catalogue. Selected: '{materials[0]['title']}'")

    # 4. Ask AI Real Academic Question
    print(f"\n[Step 4/13] Asking AI Tutor a real academic question...")
    q1 = "Explain the difference between a Binary Search Tree and an AVL Tree."
    r_tutor = client.post("/api/tutor/ask", json={
        "message": q1,
        "materialId": "general"
    }, headers=headers)
    assert r_tutor.status_code == 200, f"AI Tutor failed: {r_tutor.text}"
    tutor_res = r_tutor.json()
    conv_id = tutor_res.get("conversation_id")
    answer1 = tutor_res.get("answer")
    assert answer1 and len(answer1) > 20, "Expected comprehensive answer"
    print(f"  [PASS] AI Tutor generated answer ({len(answer1)} chars). Conversation ID: {conv_id}")

    # 5. Follow-up Question (Conversation continuity)
    print(f"\n[Step 5/13] Asking contextual follow-up question...")
    q2 = "What are the four types of tree rotations used to maintain that balance?"
    r_followup = client.post("/api/tutor/ask", json={
        "message": q2,
        "conversation_id": conv_id,
        "history": [
            {"role": "user", "content": q1},
            {"role": "assistant", "content": answer1}
        ]
    }, headers=headers)
    assert r_followup.status_code == 200, f"Followup failed: {r_followup.text}"
    answer2 = r_followup.json().get("answer")
    assert answer2 and len(answer2) > 20, "Expected followup answer"
    print(f"  [PASS] Follow-up answer generated ({len(answer2)} chars)")

    # 6. Save Explanation as Structured Notes
    print(f"\n[Step 6/13] Saving AI explanation as structured notes...")
    r_note = client.post("/api/notes", json={
        "title": "Tree Rotations in Self-Balancing AVL Trees",
        "topic": "Data Structures",
        "content": answer2,
        "key_points": [
            "Left-Left (LL) rotation: single right rotation.",
            "Right-Right (RR) rotation: single left rotation.",
            "Left-Right (LR) rotation: left rotation on child, right on parent.",
            "Right-Left (RL) rotation: right rotation on child, left on parent."
        ],
        "examples": [
            "// Left-Left case fix:\nNode* rotateRight(Node* y) {\n    Node* x = y->left;\n    y->left = x->right;\n    x->right = y;\n    return x;\n}"
        ],
        "tags": ["avl-trees", "rotations", "data-structures"]
    }, headers=headers)
    assert r_note.status_code == 201, f"Note creation failed: {r_note.text}"
    note_data = r_note.json()
    note_id = note_data["id"]
    print(f"  [PASS] Note successfully created! Note ID: {note_id}, Title: '{note_data['title']}'")

    # 7. AI Note Structure Enhancement
    print(f"\n[Step 7/13] Testing AI Note Structure Generator endpoint...")
    r_ai_notes = client.post("/api/notes/generate", json={
        "content_or_prompt": "Explain hash table collision resolution using open addressing and linear probing.",
        "topic": "Data Structures"
    }, headers=headers)
    assert r_ai_notes.status_code == 200, f"AI Note generator failed: {r_ai_notes.text}"
    ai_note_out = r_ai_notes.json()
    assert "title" in ai_note_out and "content" in ai_note_out
    print(f"  [PASS] AI Note Generator created structured note: '{ai_note_out['title']}' with {len(ai_note_out['key_points'])} key points.")

    # 8. List & Verify Notes in Library
    print(f"\n[Step 8/13] Fetching student's notes collection...")
    r_notes_list = client.get("/api/notes", headers=headers)
    assert r_notes_list.status_code == 200
    notes_list = r_notes_list.json()
    assert any(n["id"] == note_id for n in notes_list)
    print(f"  [PASS] Student has {len(notes_list)} note(s) ready for review and PDF export.")

    # 9. Take a Quiz
    print(f"\n[Step 9/13] Generating and attempting a Quiz on Data Structures...")
    r_quiz = client.post("/api/quizzes/generate", json={
        "material_id": mat_id,
        "topic": "Trees",
        "count": 3,
        "difficulty": "medium"
    }, headers=headers)
    assert r_quiz.status_code == 201, f"Quiz generation failed: {r_quiz.text}"
    quiz_id = r_quiz.json()["id"]
    questions = r_quiz.json()["questions"]
    print(f"  [PASS] Quiz generated with ID {quiz_id} ({len(questions)} questions)")

    # Start attempt
    r_attempt = client.post(f"/api/quizzes/{quiz_id}/attempt", headers=headers)
    assert r_attempt.status_code == 201
    attempt_id = r_attempt.json()["id"]

    # Submit quiz answers (intentionally answering 1 right and 2 wrong to trigger a weak topic!)
    print(f"\n[Step 10/13] Submitting quiz attempt to evaluate performance & identify weak area...")
    answers_payload = []
    for idx, q in enumerate(questions):
        # intentionally give selected_option = 0
        answers_payload.append({
            "question_id": q["id"],
            "selected_option": 0
        })

    r_submit = client.post(f"/api/quiz-attempts/{attempt_id}/submit", json={
        "answers": answers_payload
    }, headers=headers)
    assert r_submit.status_code == 200, f"Submit failed: {r_submit.text}"
    result = r_submit.json()
    accuracy = result["accuracy"]
    weak_topics = result.get("weakTopics", [])
    print(f"  [PASS] Quiz graded. Score: {result['score']}/{result['total']} ({accuracy}% accuracy).")
    print(f"  [INFO] Weak topics flagged: {weak_topics}")

    # 11. Personalized Performance & Recommendations
    print(f"\n[Step 11/13] Verifying student performance tracking & personalized recommendations...")
    r_prog = client.get("/api/progress", headers=headers)
    assert r_prog.status_code == 200
    prog_data = r_prog.json()
    print(f"  [PASS] Progress updated: Overall accuracy = {prog_data['stats']['accuracy']}%, Questions attempted = {prog_data['stats']['questionsAttempted']}")

    r_recs = client.get("/api/recommendations/today", headers=headers)
    assert r_recs.status_code == 200
    today_recs = r_recs.json()
    recs_list = today_recs.get("recommendations", [])
    print(f"  [PASS] Personalized recommendations retrieved ({len(recs_list)} recommendations). AI tip: {today_recs.get('ai_study_tip')}")

    # 12. Notifications Check
    print(f"\n[Step 12/13] Verifying student notifications...")
    r_notifs = client.get("/api/notifications", headers=headers)
    assert r_notifs.status_code == 200
    notifs_raw = r_notifs.json()
    notifs = notifs_raw.get("notifications", notifs_raw) if isinstance(notifs_raw, dict) else notifs_raw
    quiz_notif = next((n for n in notifs if n.get("type") == "quiz"), None)
    assert quiz_notif is not None, "Expected Quiz Completed notification"
    notif_msg = quiz_notif.get("body") or quiz_notif.get("message") or ""
    print(f"  [PASS] Verified notification: '{quiz_notif.get('title')}' - {notif_msg}")

    # 13. Instructor Monitoring Flow
    print(f"\n[Step 13/13] Instructor logs in to monitor student's updated performance...")
    r_inst_login = client.post("/api/auth/login", json={
        "email": "instructor@study.edu",
        "password": "password123"
    })
    assert r_inst_login.status_code == 200
    inst_token = r_inst_login.json()["access_token"]
    inst_headers = {"Authorization": f"Bearer {inst_token}"}

    # Instructor gets students list
    r_students = client.get("/api/instructor/students", headers=inst_headers)
    assert r_students.status_code == 200
    students_list = r_students.json()
    matching_student = next((s for s in students_list if s["email"] == test_email), None)
    assert matching_student is not None, "New student should appear in instructor's roster"
    print(f"  [PASS] Instructor found student in cohort roster: {matching_student['name']} (Risk: {matching_student['risk_status']})")

    # Instructor inspects student's individual detail & AI guidance
    r_detail = client.get(f"/api/instructor/students/{student_id}", headers=inst_headers)
    assert r_detail.status_code == 200
    detail = r_detail.json()
    assert str(detail["id"]) == str(student_id)
    assert len(detail.get("recent_quizzes", [])) > 0
    print(f"  [PASS] Instructor viewed detailed profile for student {detail['name']}:")
    print(f"         - Overall mastery: {detail['overall_mastery']}%")
    print(f"         - Recent quizzes recorded: {len(detail['recent_quizzes'])}")
    print(f"         - AI Instructor Guidance: {detail.get('ai_guidance', 'Guidance generated')[:100]}...")

    print("\n=================================================================")
    print("   [SUCCESS] ALL 13 FLOW STEPS PASSED THE END-TO-END AUDIT!     ")
    print("=================================================================\n")

if __name__ == "__main__":
    run_test()
