import sys
import os
import time

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

def run_tests():
    print("\n" + "="*60)
    print("RUNNING BACKEND API AND DATABASE AUTOMATED TESTS")
    print("="*60)

    with TestClient(app) as client:
        # 1. Health check
        res = client.get("/api/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print("[PASS] GET /api/health")

        # 2. Login with seeded student
        login_res = client.post("/api/auth/login", json={
            "email": "student@study.edu",
            "password": "password123"
        })
        assert login_res.status_code == 200, f"Seeded student login failed: {login_res.text}"
        login_data = login_res.json()
        assert "access_token" in login_data
        token = login_data["access_token"]
        assert login_data["user"]["email"] == "student@study.edu"
        print("[PASS] POST /api/auth/login (seeded student)")

        headers = {"Authorization": f"Bearer {token}"}

        # 3. Current user /auth/me
        me_res = client.get("/api/auth/me", headers=headers)
        assert me_res.status_code == 200, f"/auth/me failed: {me_res.text}"
        me_data = me_res.json()
        assert me_data["email"] == "student@study.edu"
        assert me_data["name"] == "Alex Mercer"
        print("[PASS] GET /api/auth/me")

        # 4. Register a new user
        test_email = f"newstudent_{int(time.time())}@college.edu"
        reg_res = client.post("/api/auth/register", json={
            "name": "Jordan Lee",
            "email": test_email,
            "password": "mypassword123",
            "role": "student"
        })
        assert reg_res.status_code == 201, f"Register failed: {reg_res.text}"
        reg_data = reg_res.json()
        assert "access_token" in reg_data
        new_token = reg_data["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}
        print("[PASS] POST /api/auth/register")

        # 5. Profile endpoints
        prof_res = client.get("/api/profile", headers=new_headers)
        assert prof_res.status_code == 200, f"Get profile failed: {prof_res.text}"
        prof_data = prof_res.json()
        assert prof_data["full_name"] == "Jordan Lee"
        assert prof_data["email"] == test_email
        print("[PASS] GET /api/profile")

        # Update profile
        update_res = client.put("/api/profile", headers=new_headers, json={
            "name": "Jordan Lee Updated",
            "bio": "Studying software engineering and AI.",
            "preferences": {"difficulty": "hard", "sessionLength": "60"}
        })
        assert update_res.status_code == 200, f"Update profile failed: {update_res.text}"
        updated_prof = update_res.json()
        assert updated_prof["full_name"] == "Jordan Lee Updated"
        assert updated_prof["preferences"]["difficulty"] == "hard"
        print("[PASS] PUT /api/profile")

        # Change password
        pwd_res = client.put("/api/profile/password", headers=new_headers, json={
            "current_password": "mypassword123",
            "new_password": "newpassword456"
        })
        assert pwd_res.status_code == 200, f"Change password failed: {pwd_res.text}"
        print("[PASS] PUT /api/profile/password")

        # Re-login with new password
        relogin_res = client.post("/api/auth/login", json={
            "email": test_email,
            "password": "newpassword456"
        })
        assert relogin_res.status_code == 200, "Login with new password failed"
        print("[PASS] Re-login with new password")

        # 6. Subjects and Topics
        sub_res = client.get("/api/subjects")
        assert sub_res.status_code == 200
        subjects = sub_res.json()
        assert len(subjects) >= 4, f"Expected at least 4 subjects, got {len(subjects)}"
        first_sub_id = subjects[0]["id"]
        print(f"[PASS] GET /api/subjects (found {len(subjects)} subjects)")

        topics_res = client.get(f"/api/subjects/{first_sub_id}/topics")
        assert topics_res.status_code == 200
        topics = topics_res.json()
        assert len(topics) > 0, "Expected topics in subject"
        print(f"[PASS] GET /api/subjects/{first_sub_id}/topics ({len(topics)} topics)")

        # 7. Materials
        mat_res = client.get("/api/materials")
        assert mat_res.status_code == 200
        materials = mat_res.json()
        assert len(materials) >= 4, f"Expected at least 4 seeded materials, got {len(materials)}"
        print(f"[PASS] GET /api/materials (found {len(materials)} materials)")

        # Create new material
        create_mat_res = client.post("/api/materials", headers=new_headers, json={
            "title": "Machine Learning Fundamentals",
            "type": "PDF",
            "pages": 85,
            "description": "Supervised and unsupervised learning basics.",
            "color": "emerald"
        })
        assert create_mat_res.status_code == 201, f"Create material failed: {create_mat_res.text}"
        created_mat = create_mat_res.json()
        mat_id = created_mat["id"]
        assert created_mat["title"] == "Machine Learning Fundamentals"
        print(f"[PASS] POST /api/materials (created ID: {mat_id})")

        # Get material by ID
        get_mat_res = client.get(f"/api/materials/{mat_id}")
        assert get_mat_res.status_code == 200
        assert get_mat_res.json()["title"] == "Machine Learning Fundamentals"
        print(f"[PASS] GET /api/materials/{mat_id}")

        # Delete material
        del_mat_res = client.delete(f"/api/materials/{mat_id}", headers=new_headers)
        assert del_mat_res.status_code == 200
        print(f"[PASS] DELETE /api/materials/{mat_id}")

        # 8. AI Service
        ai_health_res = client.get("/api/ai/health")
        assert ai_health_res.status_code == 200
        print(f"[PASS] GET /api/ai/health ({ai_health_res.json()['status']})")

        ai_test_res = client.post("/api/ai/test", headers=new_headers, json={
            "prompt": "What is the difference between an Array and a Linked List?"
        })
        assert ai_test_res.status_code == 200
        ai_data = ai_test_res.json()
        assert ai_data["success"] is True
        print(f"[PASS] POST /api/ai/test (model: {ai_data['model']})")

        # 9. RBAC & Security: Reject request without token
        unauth_res = client.get("/api/profile")
        assert unauth_res.status_code == 401
        print("[PASS] Unauthenticated request properly rejected with 401")

        # 10. Logout
        logout_res = client.post("/api/auth/logout", headers=new_headers)
        assert logout_res.status_code == 200
        print("[PASS] POST /api/auth/logout")

    print("\n" + "="*60)
    print("ALL 10 TEST SUITES PASSED SUCCESSFULLY!")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_tests()
