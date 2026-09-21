"""
Delete Material Feature Automated Verification Suite
Tests:
1. Upload study material by Student A
2. Material appears in GET /api/materials list
3. Verify cancellation simulation (material remains present)
4. Verify Student B receives 403 Forbidden when attempting to delete Student A's material
5. Student A confirms deletion: DELETE /api/materials/{id}
6. Material disappears from GET /api/materials list
7. Re-fetch / refresh: material remains deleted
8. Try opening deleted material via GET /api/materials/{id} -> 404 Not Found
9. Try querying deleted material with AI Tutor -> 404 Not Found
10. Try generating summary on deleted material -> 404 Not Found
11. Verify RAG/vector database cleanup: 0 DocumentChunks, 0 Summaries, 0 TutorInteractions, 0 SourceReferences
12. Verify unauthenticated deletion returns 401 Unauthorized
13. Verify non-existent material deletion returns 404 Not Found
"""

import sys
import os
import io
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.material import Material
from app.models.document import DocumentChunk, Summary, TutorInteraction, SourceReference

def generate_sample_pdf() -> bytes:
    p1 = "Autonomous Systems and Drone Navigation: SLAM (Simultaneous Localization and Mapping) enables robots to navigate unknown spaces."
    return f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length {len(p1) + 40} >>
stream
BT
/F1 12 Tf
72 712 Td
({p1}) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000227 00000 n 
0000000300 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
475
%%EOF""".encode("latin-1")

def test_delete_material_flow():
    print("\n" + "="*70)
    print("TESTING DELETE MATERIAL FEATURE & CASCADING RAG CLEANUP")
    print("="*70)

    with TestClient(app) as client:
        # Step A: Authenticate Student A and Student B
        print("\n[Step A] Authenticating Students...")
        login_a = client.post("/api/auth/login", json={"email": "student@study.edu", "password": "password123"})
        assert login_a.status_code == 200
        token_a = login_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}
        print("  [PASS] Student A (owner) logged in")

        student_b_email = f"student_b_{int(time.time())}@study.edu"
        reg_b = client.post("/api/auth/register", json={
            "name": "Student B",
            "email": student_b_email,
            "password": "password123",
            "role": "student"
        })
        assert reg_b.status_code == 201
        token_b = reg_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}
        print(f"  [PASS] Student B ({student_b_email}) registered")

        # Step 1: Upload Material as Student A
        print("\n[Step 1] Student A uploads study material...")
        pdf_bytes = generate_sample_pdf()
        upload_files = {"file": ("drone-navigation.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        upload_data = {
            "title": "Drone Navigation and SLAM",
            "type": "PDF",
            "description": "Autonomous robotic systems using SLAM."
        }
        up_res = client.post("/api/materials/upload", headers=headers_a, files=upload_files, data=upload_data)
        assert up_res.status_code == 201
        mat_info = up_res.json()
        mat_id = mat_info["id"]
        print(f"  [PASS] Material uploaded with ID: '{mat_id}'")

        # Generate interaction and summary so we can verify cascading cleanup
        tutor_res = client.post("/api/tutor/ask", headers=headers_a, json={
            "materialId": mat_id,
            "question": "What is SLAM?"
        })
        assert tutor_res.status_code == 200
        print("  [PASS] AI Tutor interaction generated with citations")

        sum_res = client.post("/api/summaries/generate", headers=headers_a, json={"materialId": mat_id})
        assert sum_res.status_code == 200
        print("  [PASS] Structured summary generated")

        # Step 2: Material appears in list
        print("\n[Step 2] Verifying material appears in catalogue list...")
        list_res = client.get("/api/materials", headers=headers_a)
        assert list_res.status_code == 200
        mats = list_res.json()
        assert any(m["id"] == mat_id for m in mats)
        print(f"  [PASS] Material '{mat_id}' appears in GET /api/materials")

        # Step 3: Test cancellation (simulated: do not delete, material remains)
        print("\n[Step 3] Verifying cancellation behavior...")
        # Simulating user clicking 'Cancel' in modal
        list_after_cancel = client.get("/api/materials", headers=headers_a).json()
        assert any(m["id"] == mat_id for m in list_after_cancel)
        print("  [PASS] Material remains intact when deletion is canceled")

        # Step 4: Verify Student B cannot delete Student A's material (403 Forbidden)
        print("\n[Step 4] Verifying Student B cannot delete Student A's material...")
        del_unauthorized = client.delete(f"/api/materials/{mat_id}", headers=headers_b)
        assert del_unauthorized.status_code == 403, f"Expected 403, got {del_unauthorized.status_code}"
        print("  [PASS] Student B was rejected with 403 Forbidden")

        # Step 5: Verify unauthenticated user cannot delete (401 Unauthorized)
        print("\n[Step 5] Verifying unauthenticated deletion is rejected...")
        del_no_auth = client.delete(f"/api/materials/{mat_id}")
        assert del_no_auth.status_code == 401
        print("  [PASS] Unauthenticated deletion rejected with 401 Unauthorized")

        # Step 6: Student A confirms deletion
        print("\n[Step 6] Student A confirms deletion of their own material...")
        del_success = client.delete(f"/api/materials/{mat_id}", headers=headers_a)
        assert del_success.status_code == 200
        print(f"  [PASS] DELETE /api/materials/{mat_id} returned 200 OK: {del_success.json()}")

        # Step 7: Material disappears from list
        print("\n[Step 7] Verifying material is removed from catalogue list...")
        list_after_del = client.get("/api/materials", headers=headers_a).json()
        assert not any(m["id"] == mat_id for m in list_after_del)
        print(f"  [PASS] Material '{mat_id}' is no longer in GET /api/materials")

        # Step 8: Refresh / re-fetch: remains deleted
        print("\n[Step 8] Verifying persistent deletion across refreshed requests...")
        refresh_mats = client.get("/api/materials").json()
        assert not any(m["id"] == mat_id for m in refresh_mats)
        print("  [PASS] Material persistently remains deleted")

        # Step 9: Try opening deleted material -> 404 Not Found
        print("\n[Step 9] Verifying GET /api/materials/{id} returns 404 for deleted material...")
        get_deleted = client.get(f"/api/materials/{mat_id}", headers=headers_a)
        assert get_deleted.status_code == 404
        print("  [PASS] GET /api/materials/{id} returned 404 Not Found")

        # Step 10: Verify RAG/vector data is unretrievable -> 404 Not Found
        print("\n[Step 10] Verifying AI Tutor rejects deleted material with 404...")
        tutor_deleted = client.post("/api/tutor/ask", headers=headers_a, json={
            "materialId": mat_id,
            "question": "What is SLAM?"
        })
        assert tutor_deleted.status_code == 404
        print("  [PASS] POST /api/tutor/ask returned 404 Not Found for deleted material")

        # Step 11: Verify Summary endpoint rejects deleted material -> 404 Not Found
        print("\n[Step 11] Verifying Summary endpoints reject deleted material...")
        sum_deleted = client.get(f"/api/summaries/{mat_id}", headers=headers_a)
        assert sum_deleted.status_code == 404
        print("  [PASS] GET /api/summaries/{material_id} returned 404 Not Found")

        # Step 12: Verify database cascading cleanup: zero orphaned records
        print("\n[Step 12] Verifying zero orphaned records in database...")
        db = SessionLocal()
        try:
            chunks_count = db.query(DocumentChunk).filter(DocumentChunk.material_id == mat_id).count()
            summaries_count = db.query(Summary).filter(Summary.material_id == mat_id).count()
            interactions_count = db.query(TutorInteraction).filter(TutorInteraction.material_id == mat_id).count()
            sources_count = db.query(SourceReference).filter(SourceReference.material_id == mat_id).count()

            print(f"  Chunks remaining: {chunks_count}")
            print(f"  Summaries remaining: {summaries_count}")
            print(f"  Interactions remaining: {interactions_count}")
            print(f"  Source references remaining: {sources_count}")

            assert chunks_count == 0, "Orphaned DocumentChunk records found"
            assert summaries_count == 0, "Orphaned Summary records found"
            assert interactions_count == 0, "Orphaned TutorInteraction records found"
            assert sources_count == 0, "Orphaned SourceReference records found"
            print("  [PASS] Complete cascading cleanup verified: 0 orphaned records remain")
        finally:
            db.close()

        # Step 13: Non-existent material deletion returns 404
        print("\n[Step 13] Verifying non-existent deletion returns 404...")
        del_non_existent = client.delete(f"/api/materials/non-existent-material-{int(time.time())}", headers=headers_a)
        assert del_non_existent.status_code == 404
        print("  [PASS] Deletion of non-existent material returned 404 Not Found")

    print("\n" + "="*70)
    print("ALL DELETE MATERIAL TESTS PASSED WITH 100% SUCCESS!")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_delete_material_flow()
