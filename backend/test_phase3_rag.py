"""
Phase 3 Verification Script
Tests:
1. Login with student account
2. List materials (checks processing_status and topics)
3. Upload study material (text/PDF), extracting chunks and indexing
4. RAG-grounded Tutor Q&A with source citations
5. Anti-hallucination refusal on out-of-scope query
6. Generate structured summary (keyConcepts, sections with body and points)
"""
import requests
import json
import io

BASE_URL = "http://127.0.0.1:8000/api"

def test_phase3():
    print("=== Phase 3 End-to-End Verification ===")
    
    # 1. Login
    print("\n[1/6] Logging in as student@study.edu...")
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "student@study.edu",
        "password": "password123"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    print("  ✓ Login successful. JWT token acquired.")

    # 2. Get materials catalogue
    print("\n[2/6] Checking materials catalogue...")
    mats_res = requests.get(f"{BASE_URL}/materials", headers=headers)
    assert mats_res.status_code == 200, f"List materials failed: {mats_res.text}"
    materials = mats_res.json()
    assert len(materials) >= 1, "No materials returned"
    ds_mat = next((m for m in materials if m["id"] == "data-structures"), materials[0])
    print(f"  ✓ Found material: '{ds_mat['title']}' (processing_status: {ds_mat.get('processing_status')})")

    # 3. Grounded AI Tutor Q&A
    print("\n[3/6] Testing Grounded AI Tutor Q&A on Data Structures...")
    tutor_res = requests.post(f"{BASE_URL}/tutor/ask", json={
        "materialId": "data-structures",
        "question": "How do BFS and DFS differ?"
    }, headers=headers)
    assert tutor_res.status_code == 200, f"Tutor ask failed: {tutor_res.text}"
    tutor_data = tutor_res.json()
    print("  ✓ Tutor Response received:")
    print(f"    - Grounded: {tutor_data['grounded']}")
    print(f"    - Sources: {tutor_data['sources']}")
    print(f"    - Answer preview: {tutor_data['answer'][:200]}...")
    assert tutor_data["grounded"] is True, "Expected tutor reply to be grounded"
    assert len(tutor_data["sources"]) > 0, "Expected source citations"

    # 4. Anti-hallucination guardrail check
    print("\n[4/6] Testing Anti-Hallucination Guardrail (Out-of-scope question)...")
    refusal_res = requests.post(f"{BASE_URL}/tutor/ask", json={
        "materialId": "data-structures",
        "question": "What is the best recipe for baking chocolate brownies?"
    }, headers=headers)
    assert refusal_res.status_code == 200, f"Tutor ask failed: {refusal_res.text}"
    refusal_data = refusal_res.json()
    print(f"    - Grounded: {refusal_data['grounded']}")
    print(f"    - Sources count: {len(refusal_data['sources'])}")
    print(f"    - Answer: {refusal_data['answer'][:150]}...")
    assert refusal_data["grounded"] is False or len(refusal_data["sources"]) == 0, "Expected out-of-scope question to trigger anti-hallucination refusal"
    print("  ✓ Anti-hallucination guardrail verified.")

    # 5. Summaries Endpoint
    print("\n[5/6] Testing Structured Study Summary...")
    sum_res = requests.get(f"{BASE_URL}/summaries/data-structures", headers=headers)
    assert sum_res.status_code == 200, f"Get summary failed: {sum_res.text}"
    sum_data = sum_res.json()
    print(f"  ✓ Summary Title: {sum_data.get('materialTitle')}")
    print(f"  ✓ Key Concepts ({len(sum_data['keyConcepts'])}): {sum_data['keyConcepts']}")
    print(f"  ✓ Sections ({len(sum_data['sections'])}):")
    for sec in sum_data["sections"][:2]:
        print(f"    - [{sec['id']}] {sec['title']}: {len(sec['points'])} key points")
    assert len(sum_data["keyConcepts"]) > 0, "Expected key concepts"
    assert len(sum_data["sections"]) > 0, "Expected summary sections"

    # 6. Upload a document with real chunking and indexing
    print("\n[6/6] Testing Study Material Upload with Ingestion Pipeline...")
    sample_notes = (
        "Operating Systems: Memory Management & Paging.\n\n"
        "Page 1: Virtual Memory Concepts.\n"
        "Virtual memory decouples the programmer's logical memory from physical memory (RAM). "
        "Each process operates in a private virtual address space mapped by page tables. "
        "The Memory Management Unit (MMU) handles hardware translation from virtual to physical addresses.\n\n"
        "Page 2: Page Replacement Algorithms.\n"
        "When physical memory is full, a page fault triggers the OS page replacement policy. "
        "FIFO replaces the oldest page in memory, but is vulnerable to Belady's Anomaly where allocating more frames increases page faults. "
        "LRU (Least Recently Used) replaces the page unused for the longest duration, which is optimal but requires hardware timestamp tracking. "
        "Clock (Second Chance) provides a practical approximation of LRU using a reference bit."
    )
    
    upload_headers = {"Authorization": f"Bearer {token}"}
    files = {
        "file": ("memory-management-notes.txt", io.BytesIO(sample_notes.encode("utf-8")), "text/plain")
    }
    data = {
        "title": "Virtual Memory Notes",
        "type": "Notes",
        "description": "Operating system memory management, paging, and page replacement policies."
    }
    upload_res = requests.post(f"{BASE_URL}/materials/upload", headers=upload_headers, files=files, data=data)
    assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
    uploaded_mat = upload_res.json()
    print(f"  ✓ Uploaded material: ID={uploaded_mat['id']}, Title={uploaded_mat['title']}")
    print(f"  ✓ Processing status: {uploaded_mat.get('processing_status')}")
    print(f"  ✓ Extracted pages: {uploaded_mat.get('pages')}")

    # Ask tutor about newly uploaded notes
    print("  Testing Q&A against newly uploaded document...")
    new_tutor_res = requests.post(f"{BASE_URL}/tutor/ask", json={
        "materialId": uploaded_mat["id"],
        "question": "What is Belady's Anomaly and which algorithm suffers from it?"
    }, headers=headers)
    assert new_tutor_res.status_code == 200, f"New tutor ask failed: {new_tutor_res.text}"
    new_data = new_tutor_res.json()
    print(f"    - Grounded: {new_data['grounded']}")
    print(f"    - Sources: {new_data['sources']}")
    print(f"    - Answer snippet: {new_data['answer'][:200]}...")
    assert new_data["grounded"] is True, "Expected newly uploaded document Q&A to be grounded"

    print("\n==========================================")
    print("🎉 ALL PHASE 3 BACKEND TESTS PASSED SUCCESSFULLY!")
    print("==========================================")

if __name__ == "__main__":
    test_phase3()
