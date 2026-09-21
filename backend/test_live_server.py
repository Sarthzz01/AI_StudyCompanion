import requests

BASE_URL = "http://localhost:8000/api"

def test_live_server():
    print("\n--- TESTING LIVE RUNNING BACKEND SERVER ---")
    
    # 1. Health
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("[PASS] Live Health check: 200 OK")

    # 2. Login as seeded student
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "student@study.edu",
        "password": "password123"
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    user = r.json()["user"]
    print(f"[PASS] Logged in as: {user['name']} ({user['email']})")

    headers = {"Authorization": f"Bearer {token}"}

    # 3. GET /api/auth/me
    r = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert r.status_code == 200
    print(f"[PASS] Live /auth/me verified: {r.json()['name']}")

    # 4. GET /api/profile
    r = requests.get(f"{BASE_URL}/profile", headers=headers)
    assert r.status_code == 200
    prof = r.json()
    print(f"[PASS] Live profile fetched: {prof['full_name']} | Role: {prof['role']}")

    # 5. GET /api/subjects
    r = requests.get(f"{BASE_URL}/subjects", headers=headers)
    assert r.status_code == 200
    subjects = r.json()
    print(f"[PASS] Live subjects fetched: {len(subjects)} subjects")

    # 6. GET /api/materials
    r = requests.get(f"{BASE_URL}/materials", headers=headers)
    assert r.status_code == 200
    materials = r.json()
    print(f"[PASS] Live materials fetched: {len(materials)} materials")

    # 7. GET /api/ai/health
    r = requests.get(f"{BASE_URL}/ai/health")
    assert r.status_code == 200
    print(f"[PASS] Live AI health: {r.json()['status']}")

    print("\nALL LIVE ENDPOINTS CONFIRMED WORKING ON http://localhost:8000!\n")

if __name__ == "__main__":
    test_live_server()
