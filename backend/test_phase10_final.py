"""
Phase 10 Final Verification Test Suite:
Student Analytics, Notifications System, Data Consistency, User Isolation, and Full Integration.
"""
import sys
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.study import Notification, Goal, QuizAttempt, Quiz
from app.models.learner import LearnerModel, Progress
from app.models.viva import VivaSession

client = TestClient(app)

def get_token_for_user(email: str, password: str = "password123") -> str:
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    if r.status_code != 200:
        raise Exception(f"Failed to login user {email}: {r.text}")
    return r.json()["access_token"]

def test_1_notifications_lifecycle():
    print("\n--- [TEST 1] Notifications CRUD & Lifecycle ---")
    token = get_token_for_user("student@study.edu")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch initial notifications
    r = client.get("/api/notifications", headers=headers)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    notifs = r.json()
    assert isinstance(notifs, list), "Expected list of notifications"
    print(f"  [PASS] Initial notifications fetched: {len(notifs)} items.")

    # 2. Get summary
    r_sum = client.get("/api/notifications/summary", headers=headers)
    assert r_sum.status_code == 200
    sum_data = r_sum.json()
    assert "unread_count" in sum_data
    assert "total_count" in sum_data
    print(f"  [PASS] Notifications summary: {sum_data['unread_count']} unread, {sum_data['total_count']} total.")

    # 3. Create a test notification
    r_create = client.post(
        "/api/notifications",
        json={
            "title": "Phase 10 Verification Alert",
            "message": "Testing real database notifications for student.",
            "type": "info"
        },
        headers=headers
    )
    assert r_create.status_code == 201
    created_notif = r_create.json()
    notif_id = created_notif["id"]
    assert created_notif["title"] == "Phase 10 Verification Alert"
    assert created_notif["read"] == False
    print(f"  [PASS] Created notification ID {notif_id}.")

    # 4. Mark single notification as read
    r_read = client.put(f"/api/notifications/{notif_id}/read", headers=headers)
    assert r_read.status_code == 200
    assert r_read.json()["read"] == True
    print(f"  [PASS] Notification {notif_id} marked as read.")

    # 5. Mark all as read
    r_all = client.put("/api/notifications/read-all", headers=headers)
    assert r_all.status_code == 200
    r_sum2 = client.get("/api/notifications/summary", headers=headers)
    assert r_sum2.json()["unread_count"] == 0
    print("  [PASS] Mark all notifications as read verified (unread count = 0).")

    # 6. Delete single notification
    r_del = client.delete(f"/api/notifications/{notif_id}", headers=headers)
    assert r_del.status_code == 204
    print(f"  [PASS] Notification {notif_id} deleted.")

def test_2_event_driven_notifications():
    print("\n--- [TEST 2] Event-Driven Notification Generation ---")
    token = get_token_for_user("student@study.edu")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Goal completion triggers notification
    r_goal_create = client.post(
        "/api/goals",
        json={"title": "Master Process Synchronization", "type": "weekly", "target": 3, "unit": "quizzes"},
        headers=headers
    )
    assert r_goal_create.status_code == 201
    goal_id = r_goal_create.json()["id"]

    # Mark goal completed
    r_goal_comp = client.put(f"/api/goals/{goal_id}", json={"completed": True}, headers=headers)
    assert r_goal_comp.status_code == 200

    # Verify notification created
    r_notifs = client.get("/api/notifications", headers=headers)
    assert r_notifs.status_code == 200
    notif_titles = [n["title"] for n in r_notifs.json()]
    assert "Study Goal Completed" in notif_titles
    print("  [PASS] Goal completion successfully generated real database notification.")

    # Clean up test goal
    client.delete(f"/api/goals/{goal_id}", headers=headers)

def test_3_student_analytics_and_viva_integration():
    print("\n--- [TEST 3] Unified Student Analytics & Viva Integration ---")
    token = get_token_for_user("student@study.edu")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch comprehensive progress
    r_prog = client.get("/api/progress", headers=headers)
    assert r_prog.status_code == 200
    pdata = r_prog.json()

    stats = pdata["stats"]
    assert "accuracy" in stats
    assert "questionsAttempted" in stats
    assert "studyMinutes" in stats
    assert "topicsCompleted" in stats
    assert "totalTopics" in stats
    assert "overallProgress" in stats
    assert "recallReliability" in stats
    assert "vivaSessionsCount" in stats
    assert "averageVivaScore" in stats

    print(f"  [PASS] Aggregate Stats: Accuracy={stats['accuracy']}%, Questions={stats['questionsAttempted']}, "
          f"StudyTime={stats['studyMinutes']}m, RecallReliability={stats['recallReliability']}%, "
          f"VivaSessions={stats['vivaSessionsCount']}, AvgVivaScore={stats['averageVivaScore']}%.")

    # 2. Verify vivaPerformance array
    viva_perf = pdata.get("vivaPerformance", [])
    assert isinstance(viva_perf, list)
    print(f"  [PASS] Viva performance stream contains {len(viva_perf)} records.")

    # 3. Topic progress consistency
    r_topics = client.get("/api/progress/topics", headers=headers)
    assert r_topics.status_code == 200
    t_list = r_topics.json()
    assert len(t_list) > 0
    first_topic = t_list[0]
    assert "topic" in first_topic
    assert "mastery" in first_topic
    assert "recall_reliability" in first_topic
    assert "status" in first_topic
    print(f"  [PASS] Topic Breakdown: '{first_topic['topic']}' Mastery={first_topic['mastery']}%, Status={first_topic['status']}.")

    # 4. Diagnostic Learner Model Signals
    r_lm = client.get(f"/api/learner-model/{first_topic['topic']}", headers=headers)
    assert r_lm.status_code == 200
    lm_data = r_lm.json()
    assert "signals" in lm_data
    assert "recommended_action" in lm_data
    print(f"  [PASS] Diagnostic learning signals generated for '{first_topic['topic']}': Recommended action='{lm_data['recommended_action']}'.")

def test_4_authentication_and_user_isolation():
    print("\n--- [TEST 4] Authentication & Student Data Isolation ---")
    token_a = get_token_for_user("student@study.edu")
    token_b = get_token_for_user("beatrice@study.edu")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Unauthenticated requests rejected
    r_unauth = client.get("/api/notifications")
    assert r_unauth.status_code == 401, f"Expected 401, got {r_unauth.status_code}"
    r_unauth2 = client.get("/api/progress")
    assert r_unauth2.status_code == 401
    print("  [PASS] Unauthenticated access to /api/notifications and /api/progress returns 401 Unauthorized.")

    # 2. Student A creates a private notification
    r_create_a = client.post(
        "/api/notifications",
        json={"title": "Student A Private Note", "message": "Secret data for Student A only", "type": "info"},
        headers=headers_a
    )
    assert r_create_a.status_code == 201
    notif_a_id = r_create_a.json()["id"]

    # 3. Student B checks notifications: Student A's notification MUST NOT appear
    r_b_notifs = client.get("/api/notifications", headers=headers_b)
    assert r_b_notifs.status_code == 200
    b_titles = [n["title"] for n in r_b_notifs.json()]
    assert "Student A Private Note" not in b_titles
    print("  [PASS] Student B cannot see Student A's private notifications.")

    # 4. Student B cannot delete or mark Student A's notification
    r_bad_del = client.delete(f"/api/notifications/{notif_a_id}", headers=headers_b)
    assert r_bad_del.status_code == 404, f"Expected 404 for cross-user delete, got {r_bad_del.status_code}"
    print("  [PASS] Cross-user notification modification blocked with 404.")

    # Clean up Student A's note
    client.delete(f"/api/notifications/{notif_a_id}", headers=headers_a)

def test_5_full_student_journey_integration():
    print("\n--- [TEST 5] Full Student Journey Integration Flow ---")
    token = get_token_for_user("student@study.edu")
    headers = {"Authorization": f"Bearer {token}"}

    # Verify Study Plan
    r_plan = client.get("/api/study-plan", headers=headers)
    assert r_plan.status_code == 200
    plan_data = r_plan.json()
    assert "tasks" in plan_data
    print(f"  [PASS] Daily Study Plan loaded ({len(plan_data['tasks'])} tasks).")

    # Verify Spaced Revision
    r_rev = client.get("/api/revision", headers=headers)
    assert r_rev.status_code == 200
    rev_data = r_rev.json()
    assert isinstance(rev_data, list)
    print(f"  [PASS] Spaced Repetition Mastery Matrix loaded ({len(rev_data)} topics).")

    # Verify Recommendations
    r_rec = client.get("/api/recommendations/today", headers=headers)
    assert r_rec.status_code == 200
    rec_data = r_rec.json()
    assert "recommendations" in rec_data
    print(f"  [PASS] Adaptive Recommendations loaded ({len(rec_data['recommendations'])} items).")

    # Verify Viva History
    r_viva = client.get("/api/viva/history", headers=headers)
    assert r_viva.status_code == 200
    viva_history = r_viva.json()
    assert "sessions" in viva_history
    print(f"  [PASS] AI Viva session history accessible ({len(viva_history['sessions'])} sessions).")

def test_6_duplicate_prevention_checks():
    print("\n--- [TEST 6] Duplicate Prevention Checks ---")
    token = get_token_for_user("student@study.edu")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch count
    r1 = client.get("/api/notifications", headers=headers)
    assert r1.status_code == 200
    count_1 = len(r1.json())

    # 2. Re-fetch multiple times immediately (simulating page refreshes)
    r2 = client.get("/api/notifications", headers=headers)
    r3 = client.get("/api/notifications/summary", headers=headers)
    r4 = client.get("/api/notifications", headers=headers)
    assert r4.status_code == 200
    count_2 = len(r4.json())

    assert count_1 == count_2, f"Expected notification count to remain {count_1}, but grew to {count_2}"
    print(f"  [PASS] Repeated page refreshes / API calls created 0 duplicate notifications (Count stable at {count_1}).")

    # 3. Repeat Goal completion on already completed goal
    r_goal = client.post(
        "/api/goals",
        json={"title": "Idempotency Goal Test", "type": "daily", "target": 1, "unit": "quizzes"},
        headers=headers
    )
    assert r_goal.status_code == 201
    g_id = r_goal.json()["id"]

    # Mark completed 1st time
    client.put(f"/api/goals/{g_id}", json={"completed": True}, headers=headers)
    r_after_1 = client.get("/api/notifications", headers=headers)
    c_after_1 = len(r_after_1.json())

    # Mark completed 2nd and 3rd time
    client.put(f"/api/goals/{g_id}", json={"completed": True}, headers=headers)
    client.put(f"/api/goals/{g_id}", json={"completed": True}, headers=headers)
    r_after_3 = client.get("/api/notifications", headers=headers)
    c_after_3 = len(r_after_3.json())

    assert c_after_1 == c_after_3, f"Duplicate goal notification created: {c_after_1} vs {c_after_3}"
    print("  [PASS] Repeated completion of already-completed goal creates 0 duplicate notifications.")

    # Cleanup
    client.delete(f"/api/goals/{g_id}", headers=headers)

if __name__ == "__main__":
    print("=" * 65)
    print("EXECUTING FINAL PHASE 10 VERIFICATION TEST SUITE")
    print("=" * 65)
    test_1_notifications_lifecycle()
    test_2_event_driven_notifications()
    test_3_student_analytics_and_viva_integration()
    test_4_authentication_and_user_isolation()
    test_5_full_student_journey_integration()
    test_6_duplicate_prevention_checks()
    print("\n" + "=" * 65)
    print("FINAL PHASE 10: ALL VERIFICATION CHECKS PASSED (100% SUCCESS)!")
    print("=" * 65)
