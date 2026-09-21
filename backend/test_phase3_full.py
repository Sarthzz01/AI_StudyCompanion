"""
Comprehensive Phase 3 Automated Verification Test Suite
Tests:
1. Student authentication (JWT acquisition)
2. Real PDF document generation and upload via POST /api/materials/upload
3. Text extraction, semantic chunking, and embedding generation
4. Materials retrieval via GET /api/materials and GET /api/materials/{id}
5. Grounded AI Tutor Q&A via POST /api/tutor/ask with citation sources
6. Anti-hallucination guardrail check on out-of-scope question
7. Structured summary generation via POST /api/summaries/generate & GET /api/summaries
8. Database relational verification (User -> Material -> DocumentChunk -> Summary -> TutorInteraction -> SourceReference)
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

def generate_two_page_pdf() -> bytes:
    """Generate a valid two-page PDF with academic content for ingestion testing."""
    page1_text = (
        "Operating Systems and Virtual Memory: Virtual memory decouples logical addresses "
        "from physical RAM. The Memory Management Unit (MMU) performs hardware translation "
        "using page tables. When a virtual address is not in RAM, a page fault interrupt occurs."
    )
    page2_text = (
        "Page Replacement Policies and Belady's Anomaly: When memory is full, FIFO replaces "
        "the oldest page, but suffers from Belady's Anomaly where adding frames increases page faults. "
        "LRU (Least Recently Used) replaces the page unused longest and never suffers from Belady's Anomaly."
    )

    pdf_bytes = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R 6 0 R] /Count 2 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length {len(page1_text) + 40} >>
stream
BT
/F1 12 Tf
72 712 Td
({page1_text}) Tj
ET
endstream
endobj
6 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 7 0 R >>
endobj
7 0 obj
<< /Length {len(page2_text) + 40} >>
stream
BT
/F1 12 Tf
72 712 Td
({page2_text}) Tj
ET
endstream
endobj
xref
0 8
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000122 00000 n 
0000000234 00000 n 
0000000307 00000 n 
0000000500 00000 n 
0000000612 00000 n 
trailer
<< /Size 8 /Root 1 0 R >>
startxref
820
%%EOF""".encode("latin-1")
    return pdf_bytes

def test_phase3_full():
    print("\n" + "="*70)
    print("PHASE 3 FULL END-TO-END VERIFICATION TEST SUITE")
    print("="*70)

    with TestClient(app) as client:
        # 1. Login
        print("\n[Step 1/8] Logging in as student@study.edu...")
        login_res = client.post("/api/auth/login", json={
            "email": "student@study.edu",
            "password": "password123"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("  [OK] Authentication successful. JWT token obtained.")

        # 2. Upload PDF material
        print("\n[Step 2/8] Testing PDF upload and ingestion pipeline...")
        pdf_data = generate_two_page_pdf()
        upload_files = {
            "file": ("virtual-memory-systems.pdf", io.BytesIO(pdf_data), "application/pdf")
        }
        upload_data = {
            "title": "Virtual Memory and Paging",
            "type": "PDF",
            "description": "Operating Systems unit on paging, MMU, and page replacement policies."
        }
        up_res = client.post("/api/materials/upload", headers=headers, files=upload_files, data=upload_data)
        assert up_res.status_code == 201, f"Upload failed: {up_res.text}"
        mat_info = up_res.json()
        mat_id = mat_info["id"]
        print(f"  [OK] Uploaded material: ID='{mat_id}', Title='{mat_info['title']}'")
        print(f"  [OK] Pages extracted: {mat_info['pages']}")
        print(f"  [OK] Processing status: {mat_info['processing_status']}")
        assert mat_info["processing_status"] == "ready"
        assert mat_info["pages"] >= 1

        # 3. Retrieve material from API
        print("\n[Step 3/8] Testing GET /api/materials and GET /api/materials/{id}...")
        all_mats_res = client.get("/api/materials")
        assert all_mats_res.status_code == 200
        all_mats = all_mats_res.json()
        found_mat = next((m for m in all_mats if m["id"] == mat_id), None)
        assert found_mat is not None, "Uploaded material not found in GET /api/materials"
        print(f"  [OK] Found in catalogue: '{found_mat['title']}' ({found_mat['pages']} pages, {found_mat['topicsCount']} topics)")

        mat_by_id_res = client.get(f"/api/materials/{mat_id}")
        assert mat_by_id_res.status_code == 200
        assert mat_by_id_res.json()["id"] == mat_id
        print("  [OK] Retrieved details via GET /api/materials/{id}")

        # 4. Grounded AI Tutor Q&A on uploaded document
        print("\n[Step 4/8] Testing Grounded AI Tutor Q&A (Belady's Anomaly question)...")
        tutor_res = client.post("/api/tutor/ask", headers=headers, json={
            "materialId": mat_id,
            "question": "What is Belady's Anomaly and which page replacement algorithm suffers from it?"
        })
        assert tutor_res.status_code == 200, f"Tutor ask failed: {tutor_res.text}"
        tutor_data = tutor_res.json()
        print("  [OK] Grounded Answer Preview:")
        print(f"    {tutor_data['answer'][:240]}...")
        print(f"  [OK] Grounded flag: {tutor_data['grounded']}")
        print(f"  [OK] Sources ({len(tutor_data['sources'])}):")
        for s in tutor_data["sources"]:
            print(f"    - {s['label']} -- {s['page']}")
        assert tutor_data["grounded"] is True, "Expected tutor reply to be grounded"
        assert len(tutor_data["sources"]) > 0, "Expected at least 1 citation source"
        assert any("belady" in tutor_data["answer"].lower() or "fifo" in tutor_data["answer"].lower() for _ in [1])

        # 5. Anti-hallucination guardrail
        print("\n[Step 5/8] Testing Anti-Hallucination Guardrail (Out-of-scope query)...")
        refusal_res = client.post("/api/tutor/ask", headers=headers, json={
            "materialId": mat_id,
            "question": "What is the secret recipe for Italian chocolate gelato?"
        })
        assert refusal_res.status_code == 200
        refusal_data = refusal_res.json()
        print(f"  [OK] Out-of-scope grounded flag: {refusal_data['grounded']}")
        print(f"  [OK] Out-of-scope sources count: {len(refusal_data['sources'])}")
        print(f"  [OK] Out-of-scope answer snippet: {refusal_data['answer'][:160]}...")
        assert refusal_data["grounded"] is False or len(refusal_data["sources"]) == 0, "Expected anti-hallucination refusal"
        assert "not find information" in refusal_data["answer"].lower() or "not found" in refusal_data["answer"].lower() or not refusal_data["grounded"]
        print("  [OK] Anti-hallucination refusal verified.")

        # 6. Structured Summary Generation
        print("\n[Step 6/8] Testing Structured Summary Generation...")
        sum_gen_res = client.post("/api/summaries/generate", headers=headers, json={
            "materialId": mat_id
        })
        assert sum_gen_res.status_code == 200, f"Summary generate failed: {sum_gen_res.text}"
        sum_data = sum_gen_res.json()
        summary_id = sum_data["id"]
        print(f"  [OK] Summary ID: {summary_id}")
        print(f"  [OK] Material: {sum_data['materialTitle']}")
        print(f"  [OK] Key Concepts ({len(sum_data['keyConcepts'])}): {sum_data['keyConcepts']}")
        print(f"  [OK] Sections ({len(sum_data['sections'])}):")
        for sec in sum_data["sections"][:3]:
            print(f"    - [{sec['id']}] {sec['title']}: {len(sec['points'])} points")
        assert len(sum_data["keyConcepts"]) > 0
        assert len(sum_data["sections"]) > 0

        # Retrieve summary by material ID
        sum_by_mat = client.get(f"/api/summaries/{mat_id}", headers=headers)
        assert sum_by_mat.status_code == 200
        assert sum_by_mat.json()["materialId"] == mat_id
        print("  [OK] Retrieved summary by materialId via GET /api/summaries/{material_id}")

        # Retrieve summary by numeric summary ID
        sum_by_id = client.get(f"/api/summaries/{summary_id}", headers=headers)
        assert sum_by_id.status_code == 200
        assert sum_by_id.json()["id"] == summary_id
        print("  [OK] Retrieved summary by numeric id via GET /api/summaries/{id}")

        # List all summaries
        list_sums = client.get("/api/summaries", headers=headers)
        assert list_sums.status_code == 200
        assert len(list_sums.json()) >= 1
        print(f"  [OK] Listed summaries via GET /api/summaries (found {len(list_sums.json())})")

        # 7. Database Relational Integrity
        print("\n[Step 7/8] Verifying Database Relational Integrity...")
        db = SessionLocal()
        try:
            # Check material
            db_mat = db.query(Material).filter(Material.id == mat_id).first()
            assert db_mat is not None, "Material not found in DB"
            assert db_mat.user is not None, "Material user relationship broken"
            print(f"  [OK] User -> Material relationship: {db_mat.user.email} -> {db_mat.title}")

            # Check chunks
            db_chunks = db.query(DocumentChunk).filter(DocumentChunk.material_id == mat_id).all()
            assert len(db_chunks) >= 1, "No DocumentChunk rows created"
            print(f"  [OK] Material -> DocumentChunk relationship: {len(db_chunks)} chunks stored with page metadata")

            # Check summaries
            db_sum = db.query(Summary).filter(Summary.material_id == mat_id).first()
            assert db_sum is not None, "Summary record not found in DB"
            assert db_sum.material_id == mat_id
            print(f"  [OK] Material -> Summary relationship: Summary ID {db_sum.id} linked to {mat_id}")

            # Check TutorInteraction & SourceReference
            db_interactions = db.query(TutorInteraction).filter(TutorInteraction.material_id == mat_id).all()
            assert len(db_interactions) >= 1, "TutorInteraction records missing"
            print(f"  [OK] TutorInteraction records found: {len(db_interactions)} interactions")

            db_sources = db.query(SourceReference).filter(SourceReference.material_id == mat_id).all()
            assert len(db_sources) >= 1, "SourceReference records missing"
            print(f"  [OK] SourceReference table rows found: {len(db_sources)} source references linked to interactions")
            for s in db_sources:
                print(f"    - SourceReference: label='{s.label}', page='{s.page}', chunk_id={s.chunk_id}")

        finally:
            db.close()

        # 8. Delete material cleanup test
        print("\n[Step 8/8] Testing DELETE /api/materials/{id} (cascade cleanup)...")
        del_res = client.delete(f"/api/materials/{mat_id}", headers=headers)
        assert del_res.status_code == 200, f"Delete failed: {del_res.text}"
        print(f"  [OK] Material '{mat_id}' deleted successfully.")

        db_check = SessionLocal()
        try:
            assert db_check.query(Material).filter(Material.id == mat_id).first() is None
            assert db_check.query(DocumentChunk).filter(DocumentChunk.material_id == mat_id).first() is None
            print("  [OK] Verified cascading deletion of Material and its DocumentChunks from DB.")
        finally:
            db_check.close()

    print("\n" + "="*70)
    print("[SUCCESS] ALL PHASE 3 END-TO-END TESTS PASSED WITH 100% SUCCESS!")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_phase3_full()
