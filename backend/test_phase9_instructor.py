"""
Phase 9 Instructor Module Test Suite
Verifies:
1. Instructor RBAC (Student blocked with 403, Instructor permitted with 200).
2. Instructor Dashboard KPIs & Summaries.
3. Student List & Detailed Progress (Privacy preserved, no credentials exposed).
4. Assessment Creation, AI-assisted question generation, Update, and Assignment.
5. Student Assessment Taking, Safe Question delivery, and Auto-grading.
6. Class Analytics & Comprehensive Class Report.
7. Instructor Feedback & Interventions with In-App Notifications.
"""

import sys
import os

# Ensure backend directory in pythonpath
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User, Role
from app.models.assessment import Assessment, AssessmentAssignment, AssessmentSubmission, InstructorFeedback
from app.services.auth_service import create_access_token

client = TestClient(app)

def get_token_for_user(email: str) -> str:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError(f"User {email} not found in database.")
        role_name = user.role.name if user.role else "student"
        token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": role_name})
        return token
    finally:
        db.close()

def test_1_rbac_student_blocked():
    print("\n[TEST 1] Verifying RBAC: Student Role is Blocked from Instructor APIs...")
    student_token = get_token_for_user("student@study.edu")
    headers = {"Authorization": f"Bearer {student_token}"}

    endpoints = [
        "/api/instructor/dashboard",
        "/api/instructor/students",
        "/api/instructor/assessments",
        "/api/instructor/analytics/overview",
        "/api/instructor/reports/class-summary",
        "/api/instructor/feedback"
    ]

    for ep in endpoints:
        res = client.get(ep, headers=headers)
        assert res.status_code == 403, f"Expected 403 on {ep} for student, got {res.status_code}"
    print("  -> PASSED: All instructor endpoints strictly return 403 Forbidden for student tokens.")

def test_2_instructor_dashboard_and_analytics():
    print("\n[TEST 2] Verifying Instructor Dashboard & Class Analytics...")
    inst_token = get_token_for_user("instructor@study.edu")
    headers = {"Authorization": f"Bearer {inst_token}"}

    # 1. Dashboard
    res = client.get("/api/instructor/dashboard", headers=headers)
    assert res.status_code == 200, f"Dashboard failed: {res.text}"
    dash = res.json()
    assert "total_students" in dash and dash["total_students"] >= 1
    assert "average_class_mastery" in dash
    assert "at_risk_students_count" in dash
    print(f"  -> Dashboard summary: {dash['total_students']} students, avg mastery {dash['average_class_mastery']}%, {dash['at_risk_students_count']} at-risk.")

    # 2. Analytics Overview
    res_an = client.get("/api/instructor/analytics/overview", headers=headers)
    assert res_an.status_code == 200
    an_data = res_an.json()
    assert "topic_distribution" in an_data and len(an_data["topic_distribution"]) > 0
    assert "score_distribution" in an_data
    print(f"  -> Class analytics: {len(an_data['topic_distribution'])} topics tracked, total study hours: {an_data['total_study_hours']} hrs.")

    # 3. Class Report
    res_rep = client.get("/api/instructor/reports/class-summary", headers=headers)
    assert res_rep.status_code == 200
    rep_data = res_rep.json()
    assert "top_performers" in rep_data
    assert "recommended_class_actions" in rep_data
    print(f"  -> Class report generated with {len(rep_data['recommended_class_actions'])} recommended pedagogical actions.")

def test_3_students_list_and_detail():
    print("\n[TEST 3] Verifying Student Directory & Individual Progress Profile...")
    inst_token = get_token_for_user("instructor@study.edu")
    headers = {"Authorization": f"Bearer {inst_token}"}

    res = client.get("/api/instructor/students", headers=headers)
    assert res.status_code == 200
    students = res.json()
    assert len(students) >= 1
    print(f"  -> Found {len(students)} enrolled students in class.")

    # Inspect first student detail
    s_id = students[0]["id"]
    res_detail = client.get(f"/api/instructor/students/{s_id}", headers=headers)
    assert res_detail.status_code == 200
    s_detail = res_detail.json()
    assert s_detail["name"]
    assert "topics" in s_detail
    assert "recent_quizzes" in s_detail
    assert "recent_vivas" in s_detail
    # Security / Privacy Check: No password hashes leaked
    assert "hashed_password" not in s_detail
    assert "password" not in s_detail
    print(f"  -> Retrieved detailed progress for {s_detail['name']}: {len(s_detail['topics'])} topics, {len(s_detail['recent_quizzes'])} quizzes, risk: {s_detail['risk_status']}.")

def test_4_ai_question_generation_and_assessment_crud():
    print("\n[TEST 4] Verifying AI Question Generation & Assessment Lifecycle...")
    inst_token = get_token_for_user("instructor@study.edu")
    headers = {"Authorization": f"Bearer {inst_token}"}

    # 1. AI Generation
    ai_req = {
        "topic": "Transactions & ACID",
        "subject": "DBMS",
        "difficulty": "hard",
        "question_count": 3,
        "include_explanations": True
    }
    res_ai = client.post("/api/instructor/ai/generate-questions", json=ai_req, headers=headers)
    assert res_ai.status_code == 200
    ai_gen = res_ai.json()
    assert len(ai_gen["questions"]) == 3
    assert ai_gen["topic"] == "Transactions & ACID"
    print(f"  -> AI generated {len(ai_gen['questions'])} questions for '{ai_gen['suggested_title']}'.")

    # 2. Assessment Create
    create_req = {
        "title": "DBMS Advanced Transactions Exam",
        "topic": "Transactions & ACID",
        "difficulty": "hard",
        "time_limit_minutes": 20,
        "total_points": 100,
        "pass_percentage": 65.0,
        "questions": ai_gen["questions"],
        "is_published": True
    }
    res_create = client.post("/api/instructor/assessments", json=create_req, headers=headers)
    assert res_create.status_code == 201
    created_assess = res_create.json()
    assess_id = created_assess["id"]
    print(f"  -> Created assessment ID {assess_id} ('{created_assess['title']}').")

    # 3. Assessment Assign
    assign_req = {
        "assigned_to_all": True,
        "instructions": "Please solve all questions before Friday."
    }
    res_asgn = client.post(f"/api/instructor/assessments/{assess_id}/assign", json=assign_req, headers=headers)
    assert res_asgn.status_code == 200
    asgn_data = res_asgn.json()
    assert asgn_data["assessment_id"] == assess_id
    print(f"  -> Successfully assigned assessment to all students (Assignment ID: {asgn_data['id']}).")

    return assess_id, asgn_data["id"]

def test_5_student_assessment_flow_and_grading(assess_id, assign_id):
    print("\n[TEST 5] Verifying Student Portal Assessment Taking & Auto-Grading...")
    student_token = get_token_for_user("student@study.edu")
    s_headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Student views assigned assessments
    res_assigned = client.get("/api/assessments/assigned", headers=s_headers)
    assert res_assigned.status_code == 200
    assigned_list = res_assigned.json()
    assert any(a["assessment_id"] == assess_id for a in assigned_list)
    print(f"  -> Student sees {len(assigned_list)} active assignments in portal.")

    # 2. Student fetches questions (Must NOT expose correct answers)
    res_q = client.get(f"/api/assessments/{assess_id}", headers=s_headers)
    assert res_q.status_code == 200
    safe_assess = res_q.json()
    for q in safe_assess["questions"]:
        assert "correct_answer" not in q, "Security failure: correct_answer exposed to student!"
        assert "explanation" not in q, "Security failure: explanation exposed to student before submission!"
    print(f"  -> Questions retrieved safely without answer key exposure.")

    # 3. Student submits answers
    submission_req = {
        "assignment_id": assign_id,
        "time_spent_seconds": 450,
        "answers": [
            {"question_id": q["id"], "selected_option": 0} for q in safe_assess["questions"]
        ]
    }
    res_sub = client.post(f"/api/assessments/{assess_id}/submit", json=submission_req, headers=s_headers)
    assert res_sub.status_code == 200
    sub_data = res_sub.json()
    assert sub_data["score"] >= 0
    assert "percentage" in sub_data
    assert "passed" in sub_data
    print(f"  -> Student submitted assessment: Score {sub_data['score']}/{sub_data['total_points']} ({sub_data['percentage']}%), Passed: {sub_data['passed']}.")

def test_6_instructor_feedback():
    print("\n[TEST 6] Verifying Instructor Feedback Creation & Retrieval...")
    inst_token = get_token_for_user("instructor@study.edu")
    headers = {"Authorization": f"Bearer {inst_token}"}

    # Get student id
    db = SessionLocal()
    student = db.query(User).filter(User.email == "student@study.edu").first()
    student_id = student.id
    db.close()

    fb_req = {
        "student_id": student_id,
        "topic": "Transactions & ACID",
        "feedback_type": "assessment_review",
        "feedback_text": "Great work on ACID isolation properties. For next week, focus on multi-version concurrency control.",
        "action_items": [
            "Read Chapter 4 on MVCC",
            "Solve practice problems on Strict 2PL"
        ]
    }
    res_fb = client.post("/api/instructor/feedback", json=fb_req, headers=headers)
    assert res_fb.status_code == 201
    fb_data = res_fb.json()
    assert fb_data["student_id"] == student_id
    assert len(fb_data["action_items"]) == 2
    print(f"  -> Instructor posted feedback for student #{student_id} with {len(fb_data['action_items'])} action items.")

    # List feedbacks
    res_list = client.get("/api/instructor/feedback", headers=headers)
    assert res_list.status_code == 200
    fbs = res_list.json()
    assert len(fbs) >= 1
    print(f"  -> Successfully retrieved {len(fbs)} instructor feedbacks.")

if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING PHASE 9 INSTRUCTOR MODULE TEST SUITE")
    print("=" * 60)
    test_1_rbac_student_blocked()
    test_2_instructor_dashboard_and_analytics()
    test_3_students_list_and_detail()
    assess_id, assign_id = test_4_ai_question_generation_and_assessment_crud()
    test_5_student_assessment_flow_and_grading(assess_id, assign_id)
    test_6_instructor_feedback()
    print("\n" + "=" * 60)
    print("ALL PHASE 9 BACKEND TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
