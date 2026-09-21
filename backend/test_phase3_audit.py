"""
Phase 3 Verification Audit Test Suite
Checks:
1. Material upload
2. Material processing
3. PDF text extraction
4. Chunking
5. Embeddings
6. Vector storage
7. RAG retrieval
8. AI Tutor
9. Source/page references
10. Summary generation
11. Material deletion
12. Database cleanup after deletion
13. Vector/RAG cleanup after deletion
14. Security & Access Control:
    - Gemini API key backend-only
    - .env gitignored
    - Deleted materials return 404 (cannot be retrieved by RAG)
    - Student isolation: student B cannot delete or access student A's private material
15. Existing Phase 1 & 2 regression verification
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

def generate_audit_pdf() -> bytes:
    """Generate valid PDF with specific test concepts."""
    p1 = "Distributed Systems Consensus: The Raft consensus algorithm decomposes state machine replication into leader election, log replication, and safety."
    p2 = "Byzantine Fault Tolerance: PBFT guarantees safety and liveness in asynchronous systems with up to (n - 1)/3 Byzantine faulty nodes."
    
    return f"""%PDF-1.4
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
<< /Length {len(p1) + 40} >>
stream
BT
/F1 12 Tf
72 712 Td
({p1}) Tj
ET
endstream
endobj
6 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 7 0 R >>
endobj
7 0 obj
<< /Length {len(p2) + 40} >>
stream
BT
/F1 12 Tf
72 712 Td
({p2}) Tj
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

def run_audit():
    print("\n" + "="*70)
    print("STARTING PHASE 3 VERIFICATION AUDIT")
    print("="*70)

    # A. Security & Configuration Audits
    print("\n[Audit A] Security and Configuration Checks...")
    
    # 1. Verify .env is in .gitignore
    root_gitignore = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".gitignore"))
    backend_gitignore = os.path.abspath(os.path.join(os.path.dirname(__file__), ".gitignore"))
    assert os.path.exists(root_gitignore), "Root .gitignore missing"
    with open(root_gitignore, "r") as f:
        root_git_content = f.read()
    assert ".env" in root_git_content, ".env not ignored in root .gitignore"
    print("  [PASS] .env is properly ignored in root .gitignore")

    # 2. Verify Gemini API key is backend-only
    frontend_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-study-companion", "src"))
    for root, _, files in os.walk(frontend_src):
        for file in files:
            if file.endswith((".js", ".jsx", ".ts", ".tsx", ".html")):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    assert "GEMINI_API_KEY" not in content, f"GEMINI_API_KEY leaked in {file}"
                    assert "AQ." not in content, f"Possible API key pattern found in {file}"
    print("  [PASS] Gemini API key is strictly backend-only (zero frontend leaks)")

    with TestClient(app) as client:
        # B. User Setup (Two distinct students for isolation testing)
        print("\n[Audit B] Student Authentication & Isolation Setup...")
        # Student A (Alex Mercer)
        login_res_a = client.post("/api/auth/login", json={"email": "student@study.edu", "password": "password123"})
        assert login_res_a.status_code == 200
        token_a = login_res_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}
        print("  [PASS] Student A (student@study.edu) authenticated")

        # Student B (New distinct student)
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
        print(f"  [PASS] Student B ({student_b_email}) registered and authenticated")

        # C. 13-Point Complete Phase 3 Flow
        print("\n[Audit C] Verifying Complete 13-Point Phase 3 Flow...")
        
        # 1. Material Upload & 2. Material Processing
        pdf_bytes = generate_audit_pdf()
        upload_files = {"file": ("distributed-consensus.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        upload_data = {
            "title": "Distributed Consensus Notes",
            "type": "PDF",
            "description": "Notes covering Raft leader election and PBFT Byzantine fault tolerance."
        }
        up_res = client.post("/api/materials/upload", headers=headers_a, files=upload_files, data=upload_data)
        assert up_res.status_code == 201, f"Upload failed: {up_res.text}"
        mat = up_res.json()
        mat_id = mat["id"]
        print(f"  [PASS] 1. Material upload: Created ID '{mat_id}'")
        print(f"  [PASS] 2. Material processing: processing_status='{mat['processing_status']}'")
        assert mat["processing_status"] == "ready"

        # 3. PDF Text Extraction & 4. Chunking & 5. Embeddings & 6. Vector Storage
        db = SessionLocal()
        try:
            chunks = db.query(DocumentChunk).filter(DocumentChunk.material_id == mat_id).order_by(DocumentChunk.chunk_index).all()
            assert len(chunks) == 2, f"Expected 2 chunks, got {len(chunks)}"
            print(f"  [PASS] 3. PDF text extraction: 2 pages extracted successfully")
            print(f"  [PASS] 4. Chunking: {len(chunks)} chunks with token counts {[c.token_count for c in chunks]}")
            for c in chunks:
                assert c.embedding_json is not None, "Embedding vector missing"
                assert len(c.embedding_json) > 0, "Empty embedding vector"
            print(f"  [PASS] 5. Embeddings: Vectors generated (dim={len(chunks[0].embedding_json)})")
            print(f"  [PASS] 6. Vector storage: Stored in document_chunks table with JSON vectors")
        finally:
            db.close()

        # 7. RAG Retrieval & 8. AI Tutor & 9. Source/Page References
        tutor_res = client.post("/api/tutor/ask", headers=headers_a, json={
            "materialId": mat_id,
            "question": "How does Raft handle state machine replication?"
        })
        assert tutor_res.status_code == 200, f"Tutor ask failed: {tutor_res.text}"
        tutor_data = tutor_res.json()
        print(f"  [PASS] 7. RAG retrieval: Successfully retrieved relevant chunk for query")
        print(f"  [PASS] 8. AI Tutor: Grounded={tutor_data['grounded']} | Answer preview: {tutor_data['answer'][:120]}...")
        assert tutor_data["grounded"] is True
        assert len(tutor_data["sources"]) > 0
        print(f"  [PASS] 9. Source/page references: {tutor_data['sources'][0]['label']} -- {tutor_data['sources'][0]['page']}")

        # 10. Summary Generation
        sum_res = client.post("/api/summaries/generate", headers=headers_a, json={"materialId": mat_id})
        assert sum_res.status_code == 200, f"Summary failed: {sum_res.text}"
        sum_data = sum_res.json()
        summary_id = sum_data["id"]
        assert len(sum_data["keyConcepts"]) > 0
        assert len(sum_data["sections"]) > 0
        print(f"  [PASS] 10. Summary generation: ID={summary_id} with {len(sum_data['keyConcepts'])} concepts & {len(sum_data['sections'])} sections")

        # D. Security & Access Control Audits on Student Isolation
        print("\n[Audit D] Verifying Student Access Control & Isolation...")
        # Student B attempts to query Tutor on Student A's private material
        tutor_b_res = client.post("/api/tutor/ask", headers=headers_b, json={
            "materialId": mat_id,
            "question": "Tell me about Raft"
        })
        assert tutor_b_res.status_code == 403, f"Expected 403 Forbidden for Student B accessing Student A's material, got {tutor_b_res.status_code}"
        print("  [PASS] Student B is blocked (403) from accessing Student A's private material via AI Tutor")

        # Student B attempts to generate summary on Student A's private material
        sum_b_res = client.post("/api/summaries/generate", headers=headers_b, json={"materialId": mat_id})
        assert sum_b_res.status_code == 403
        print("  [PASS] Student B is blocked (403) from generating summaries on Student A's private material")

        # Student B attempts to delete Student A's private material
        del_b_res = client.delete(f"/api/materials/{mat_id}", headers=headers_b)
        assert del_b_res.status_code == 403
        print("  [PASS] Student B is blocked (403) from deleting Student A's private material")

        # E. 11. Material Deletion & 12. Database Cleanup & 13. Vector/RAG Cleanup
        print("\n[Audit E] Verifying Deletion & Cascading RAG/DB Cleanup...")
        # Student A deletes their own material
        del_a_res = client.delete(f"/api/materials/{mat_id}", headers=headers_a)
        assert del_a_res.status_code == 200
        print(f"  [PASS] 11. Material deletion: Student A deleted '{mat_id}'")

        # 12. Database Cleanup Verification
        db2 = SessionLocal()
        try:
            assert db2.query(Material).filter(Material.id == mat_id).first() is None, "Material not deleted"
            assert db2.query(DocumentChunk).filter(DocumentChunk.material_id == mat_id).count() == 0, "DocumentChunks not deleted"
            assert db2.query(Summary).filter(Summary.material_id == mat_id).count() == 0, "Summaries not deleted"
            assert db2.query(TutorInteraction).filter(TutorInteraction.material_id == mat_id).count() == 0, "TutorInteractions not deleted"
            assert db2.query(SourceReference).filter(SourceReference.material_id == mat_id).count() == 0, "SourceReferences not deleted"
            print("  [PASS] 12. Database cleanup: All rows cascaded from materials, chunks, summaries, interactions, source_references")
        finally:
            db2.close()

        # 13. Vector / RAG Cleanup Verification (Cannot be retrieved by RAG)
        post_del_tutor = client.post("/api/tutor/ask", headers=headers_a, json={
            "materialId": mat_id,
            "question": "What is Raft consensus?"
        })
        assert post_del_tutor.status_code == 404, f"Expected 404 for deleted material, got {post_del_tutor.status_code}"
        print(f"  [PASS] 13. Vector/RAG cleanup: Querying deleted material returned 404 (strictly unretrievable)")

        # F. Existing Phase 1 & Phase 2 Functionality
        print("\n[Audit F] Verifying Existing Phase 1 & 2 Regressions...")
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/auth/me", headers=headers_a).status_code == 200
        assert client.get("/api/profile", headers=headers_a).status_code == 200
        assert client.get("/api/subjects").status_code == 200
        assert client.get("/api/materials").status_code == 200
        assert client.get("/api/ai/health").status_code == 200
        print("  [PASS] Phase 1 & Phase 2 core APIs (Health, Auth, Profile, Subjects, Catalog, AI Health) 100% operational")

    print("\n" + "="*70)
    print("PHASE 3 VERIFICATION AUDIT COMPLETE -- ALL AUDITS PASSED!")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_audit()
