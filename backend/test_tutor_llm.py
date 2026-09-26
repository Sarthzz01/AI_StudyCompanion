import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test_tutor_integration():
    print("\n--- TESTING AI TUTOR LLM INTEGRATION OVER HTTP ---")

    # 1. Login
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "student@study.edu",
        "password": "password123"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] 1. Student authenticated successfully.")

    # 2. General Science Question: What is photosynthesis?
    print("\nSending question: 'What is photosynthesis?'")
    q1_res = requests.post(f"{BASE_URL}/tutor/ask", json={
        "message": "What is photosynthesis?"
    }, headers=headers)
    assert q1_res.status_code == 200, f"Q1 failed: {q1_res.text}"
    ans1 = q1_res.json()
    assert "answer" in ans1, "Missing answer key in response"
    assert len(ans1["answer"]) > 50
    print(f"[PASS] 2. Science Question Answered ({len(ans1['answer'])} chars):")
    print(ans1["answer"][:180] + "...")

    # 3. Follow-up Question with conversation history
    print("\nSending follow-up question: 'What role does chlorophyll play in it?'")
    history = [
        {"role": "user", "content": "What is photosynthesis?"},
        {"role": "assistant", "content": ans1["answer"]}
    ]
    q2_res = requests.post(f"{BASE_URL}/tutor/ask", json={
        "message": "What role does chlorophyll play in it?",
        "history": history
    }, headers=headers)
    assert q2_res.status_code == 200, f"Q2 failed: {q2_res.text}"
    ans2 = q2_res.json()
    assert "answer" in ans2
    print(f"[PASS] 3. Follow-up Answered ({len(ans2['answer'])} chars):")
    print(ans2["answer"][:180] + "...")

    # 4. Programming Question
    print("\nSending question: 'Explain binary search in Python with code.'")
    q3_res = requests.post(f"{BASE_URL}/tutor/ask", json={
        "message": "Explain binary search in Python with code."
    }, headers=headers)
    assert q3_res.status_code == 200
    ans3 = q3_res.json()
    assert "def " in ans3["answer"] or "binary" in ans3["answer"].lower()
    print(f"[PASS] 4. Programming Question Answered:")
    print(ans3["answer"][:180] + "...")

    # 5. History retrieval
    hist_res = requests.get(f"{BASE_URL}/tutor/history", headers=headers)
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert len(hist) >= 3
    print(f"[PASS] 5. Conversation History Verified ({len(hist)} items stored in database).")

    print("\nALL AI TUTOR INTEGRATION TESTS PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    test_tutor_integration()
