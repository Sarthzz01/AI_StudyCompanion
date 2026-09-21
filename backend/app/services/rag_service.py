import io
import re
import math
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session
from app.config import settings
from app.services.ai_service import ai_service
from app.models.document import DocumentChunk, Summary, TutorInteraction, SourceReference
from app.models.material import Material
from app.models.user import User

logger = logging.getLogger("uvicorn.error")

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute pure-Python cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)

def compute_keyword_overlap_score(query: str, text: str) -> float:
    """Compute lexical term overlap between query and text as a hybrid retrieval signal."""
    stop_words = {"a", "an", "the", "is", "are", "was", "were", "and", "or", "in", "on", "at", "to", "for", "of", "with", "by", "how", "what", "why", "explain", "does", "do", "can"}
    query_tokens = [w for w in re.findall(r"\b\w+\b", query.lower()) if w not in stop_words and len(w) > 2]
    if not query_tokens:
        return 0.0
    text_lower = text.lower()
    matches = sum(1 for token in query_tokens if token in text_lower)
    return matches / len(query_tokens)

class RAGService:
    def __init__(self):
        self.embedding_model = "gemini-embedding-001"
        self.chunk_size = 600
        self.chunk_overlap = 100

    def extract_text_from_file(self, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF or text-based documents.
        Returns a list of dicts: [{'page_number': int, 'text': str}]
        """
        pages = []
        is_pdf = filename.lower().endswith(".pdf") or file_bytes.startswith(b"%PDF")

        if is_pdf:
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                for idx, page in enumerate(reader.pages):
                    raw_text = page.extract_text() or ""
                    cleaned = self._clean_text(raw_text)
                    if cleaned:
                        pages.append({"page_number": idx + 1, "text": cleaned})
            except Exception as e:
                logger.error(f"Error extracting PDF text from {filename}: {e}")
                raise ValueError(f"Could not parse PDF content: {str(e)}")
        else:
            # Plain text, markdown, notes
            try:
                decoded = file_bytes.decode("utf-8", errors="replace")
            except Exception:
                decoded = file_bytes.decode("latin-1", errors="replace")

            cleaned = self._clean_text(decoded)
            if cleaned:
                # Divide long text files into synthetic pages of ~2000 characters
                step = 2000
                total_len = len(cleaned)
                if total_len <= step:
                    pages.append({"page_number": 1, "text": cleaned})
                else:
                    page_num = 1
                    for start in range(0, total_len, step):
                        pages.append({"page_number": page_num, "text": cleaned[start:start+step]})
                        page_num += 1

        if not pages:
            # If empty, provide minimal fallback page
            pages.append({"page_number": 1, "text": "Empty document or text could not be extracted."})

        return pages

    def _clean_text(self, text: str) -> str:
        """Strip control characters, replace odd linebreaks, and collapse whitespace."""
        if not text:
            return ""
        # Remove null characters and standard terminal escape sequences
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Normalize carriage returns
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse multiple spaces or multiple blank lines
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def chunk_pages(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Split page texts into overlapping chunks while preserving page numbers.
        """
        chunks = []
        chunk_idx = 0

        for page in pages:
            page_num = page["page_number"]
            page_text = page["text"]
            if not page_text:
                continue

            # Break text into paragraphs or sentences
            start = 0
            text_len = len(page_text)

            while start < text_len:
                end = min(start + self.chunk_size, text_len)
                # If we're not at the end of the text, try to break at a sentence or word boundary
                if end < text_len:
                    last_space = page_text.rfind(" ", start + self.chunk_size // 2, end)
                    if last_space != -1:
                        end = last_space

                chunk_content = page_text[start:end].strip()
                if chunk_content:
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "page_number": page_num,
                        "content": chunk_content,
                        "token_count": len(chunk_content.split())
                    })
                    chunk_idx += 1

                # Move start forward by chunk_size - overlap
                if end >= text_len:
                    break
                start = max(start + 1, end - self.chunk_overlap)

        return chunks

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors using Gemini API (gemini-embedding-001).
        Fallback to a normalized deterministic representation if offline.
        """
        if not texts:
            return []

        embeddings: List[List[float]] = []

        if ai_service.is_configured() and ai_service.client:
            # Batch up to 30 chunks per request
            batch_size = 30
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                try:
                    res = ai_service.client.models.embed_content(
                        model=self.embedding_model,
                        contents=batch
                    )
                    for emb in res.embeddings:
                        embeddings.append(emb.values)
                except Exception as e:
                    logger.warning(f"Gemini batch embedding error: {e}. Using deterministic fallback for batch.")
                    for text in batch:
                        embeddings.append(self._fallback_embedding(text))
        else:
            for text in texts:
                embeddings.append(self._fallback_embedding(text))

        return embeddings

    def _fallback_embedding(self, text: str, dim: int = 128) -> List[float]:
        """Simple deterministic term-hash vector for offline or error resilience."""
        vec = [0.0] * dim
        tokens = re.findall(r"\w+", text.lower())
        for token in tokens:
            idx = hash(token) % dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single search query."""
        results = self.generate_embeddings([query])
        return results[0] if results else []

    def index_material(
        self,
        db: Session,
        material: Material,
        file_bytes: bytes,
        filename: str
    ) -> int:
        """
        Extracts, chunks, embeds, and indexes a study material file into DocumentChunk records.
        """
        # 1. Extract pages
        pages = self.extract_text_from_file(file_bytes, filename)
        max_page = max((p["page_number"] for p in pages), default=1)
        material.pages = max(material.pages or 0, max_page)
        material.raw_filename = filename
        material.processing_status = "processing"
        db.commit()

        # 2. Chunk text
        chunks_data = self.chunk_pages(pages)
        if not chunks_data:
            chunks_data = [{
                "chunk_index": 0,
                "page_number": 1,
                "content": material.description or material.title,
                "token_count": len((material.description or material.title).split())
            }]

        # 3. Generate embeddings
        texts = [c["content"] for c in chunks_data]
        embeddings = self.generate_embeddings(texts)

        # 4. Remove previous chunks if re-uploading
        db.query(DocumentChunk).filter(DocumentChunk.material_id == material.id).delete()

        # 5. Insert DocumentChunk records
        for i, c in enumerate(chunks_data):
            emb = embeddings[i] if i < len(embeddings) else None
            chunk_rec = DocumentChunk(
                material_id=material.id,
                chunk_index=c["chunk_index"],
                page_number=c["page_number"],
                content=c["content"],
                token_count=c["token_count"],
                embedding_json=emb
            )
            db.add(chunk_rec)

        # 6. Extract simple topics if material has default topics
        if len(pages) > 0 and len(material.topics_json or []) <= 1:
            extracted_topics = self._extract_initial_topics(material.title, [p["text"] for p in pages[:5]])
            if extracted_topics:
                material.topics_json = extracted_topics
                material.topics_count = len(extracted_topics)

        material.processing_status = "ready"
        material.last_studied = "Just now"
        db.commit()
        db.refresh(material)

        logger.info(f"Successfully indexed material '{material.id}' with {len(chunks_data)} chunks across {max_page} pages.")
        return len(chunks_data)

    def _extract_initial_topics(self, title: str, sample_texts: List[str]) -> List[Dict[str, Any]]:
        """Identify key topics from material sample text."""
        combined = f"Title: {title}\n" + "\n".join(sample_texts[:3])
        if ai_service.is_configured() and ai_service.client:
            prompt = (
                f"Extract 4 to 6 concise academic topic names from this study material snippet.\n\n"
                f"{combined[:3000]}\n\n"
                f"Return JSON: {{\"topics\": [\"Topic 1\", \"Topic 2\", ...]}}"
            )
            try:
                from google.genai import types
                cfg = types.GenerateContentConfig(response_mime_type="application/json")
                res = ai_service.client.models.generate_content(
                    model=ai_service.model_name,
                    contents=prompt,
                    config=cfg
                )
                parsed = json.loads(res.text)
                topic_names = parsed.get("topics", [])
                if topic_names:
                    return [{"name": name, "progress": 0} for name in topic_names[:8]]
            except Exception as e:
                logger.warning(f"Topic extraction with Gemini failed: {e}")

        # Fallback topics
        return [
            {"name": f"{title} Core Principles", "progress": 0},
            {"name": f"{title} Methodology & Applications", "progress": 0}
        ]

    def search_chunks(
        self,
        db: Session,
        material_id: Optional[str],
        query: str,
        top_k: int = 4
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Perform hybrid vector + keyword similarity search over chunks for a material.
        """
        chunk_query = db.query(DocumentChunk)
        if material_id:
            chunk_query = chunk_query.filter(DocumentChunk.material_id == material_id)

        all_chunks = chunk_query.all()
        if not all_chunks:
            # If no chunks in db for this material yet, check if material exists and create synthetic chunk from description
            if material_id:
                mat = db.query(Material).filter(Material.id == material_id).first()
                if mat:
                    synthetic_chunk = DocumentChunk(
                        material_id=mat.id,
                        chunk_index=0,
                        page_number=1,
                        content=f"{mat.title}\n\n{mat.description}\n\nKey topics covered: " + ", ".join([t.get("name", "") for t in (mat.topics_json or [])]),
                        token_count=50,
                        embedding_json=None
                    )
                    db.add(synthetic_chunk)
                    db.commit()
                    all_chunks = [synthetic_chunk]

        if not all_chunks:
            return []

        query_emb = self.embed_query(query)
        scored_chunks = []

        for chunk in all_chunks:
            # 1. Cosine similarity
            sem_sim = 0.0
            if query_emb and chunk.embedding_json:
                sem_sim = cosine_similarity(query_emb, chunk.embedding_json)

            # 2. Keyword overlap
            lex_score = compute_keyword_overlap_score(query, chunk.content)

            # Combined hybrid score (70% semantic, 30% lexical if semantic available)
            if query_emb and chunk.embedding_json:
                total_score = (0.7 * sem_sim) + (0.3 * lex_score)
            else:
                total_score = lex_score

            scored_chunks.append((chunk, total_score, sem_sim, lex_score))

        # Sort descending by total score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return [(c, score) for c, score, _, _ in scored_chunks[:top_k]]

    def ask_grounded_tutor(
        self,
        db: Session,
        user: User,
        question: str,
        material_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate grounded answers based strictly on retrieved chunks with citation sources.
        Guards strictly against out-of-material hallucinations.
        """
        # 1. Retrieve relevant material chunks
        mat = None
        if material_id:
            mat = db.query(Material).filter(Material.id == material_id).first()

        material_title = mat.title if mat else "Selected Study Material"
        relevant_chunks = self.search_chunks(db, material_id=material_id, query=question, top_k=4)

        # 2. Anti-hallucination check
        # Check if any chunk has reasonable relevance
        has_relevance = False
        if relevant_chunks:
            top_chunk, top_score = relevant_chunks[0]
            kw_overlap = compute_keyword_overlap_score(question, top_chunk.content)
            # Require either high semantic similarity (> 0.58) or keyword match (> 0.0) with moderate similarity (> 0.48)
            if top_score >= 0.58 or (kw_overlap > 0.0 and top_score >= 0.45):
                has_relevance = True

        if not has_relevance:
            refusal_message = (
                f"I could not find information about '{question}' in the study material for '{material_title}'. "
                f"Please refer to material covering this topic or ask a question directly related to this document."
            )
            # Record interaction
            interaction = TutorInteraction(
                user_id=user.id,
                material_id=material_id or "general",
                question=question,
                answer=refusal_message,
                grounded=False,
                sources_json=[]
            )
            db.add(interaction)
            db.commit()

            return {
                "answer": refusal_message,
                "sources": [],
                "grounded": False
            }

        # 3. Assemble Grounded Context Excerpts
        context_blocks = []
        sources = []
        seen_pages = set()

        for chunk, score in relevant_chunks:
            page_label = f"Page {chunk.page_number}"
            context_blocks.append(f"[Excerpt from {page_label}]:\n{chunk.content}")
            if chunk.page_number not in seen_pages:
                sources.append({
                    "label": f"{material_title}.pdf" if not material_title.endswith(".pdf") else material_title,
                    "page": page_label,
                    "page_number": chunk.page_number,
                    "chunk_id": chunk.id
                })
                seen_pages.add(chunk.page_number)

        joined_context = "\n\n---\n\n".join(context_blocks)

        system_instruction = (
            "You are an expert AI Academic Tutor for the AI Study Companion.\n"
            "Your task is to answer the student's question using ONLY the provided study material excerpts.\n\n"
            "STRICT RULES:\n"
            "1. Base your answer strictly on the provided excerpts.\n"
            "2. Do NOT hallucinate facts, definitions, or equations not found in the text.\n"
            "3. If the answer is only partially answered in the excerpts, provide what is stated and note what is missing.\n"
            "4. Provide a structured, pedagogically clear answer with bullet points and step-by-step clarity where helpful.\n"
            "5. Cite the relevant page numbers inline or at the end where appropriate (e.g. [Page X])."
        )

        user_prompt = (
            f"Study Material: {material_title}\n\n"
            f"Document Excerpts:\n{joined_context}\n\n"
            f"Student Question: {question}\n\n"
            f"Grounded Answer:"
        )

        ai_response = ai_service.generate_text(
            prompt=user_prompt,
            system_instruction=system_instruction
        )

        answer_text = ai_response.get("reply", "")
        if not answer_text or not ai_response.get("success"):
            # Fallback based on top chunk content
            answer_text = f"According to {material_title}:\n\n{relevant_chunks[0][0].content}"

        is_grounded = True
        lower_ans = answer_text.lower()
        if any(phrase in lower_ans for phrase in [
            "no information regarding",
            "not mentioned in the provided",
            "could not find information",
            "not found in the provided",
            "no mention of"
        ]):
            is_grounded = False
            sources = []

        # 4. Save interaction to database
        interaction = TutorInteraction(
            user_id=user.id,
            material_id=material_id or "general",
            question=question,
            answer=answer_text,
            grounded=is_grounded,
            sources_json=sources
        )
        db.add(interaction)
        db.flush()

        if is_grounded and sources:
            for s in sources:
                src_ref = SourceReference(
                    tutor_interaction_id=interaction.id,
                    material_id=material_id,
                    chunk_id=s.get("chunk_id"),
                    label=s["label"],
                    page=s.get("page"),
                    page_number=s.get("page_number")
                )
                db.add(src_ref)

        db.commit()

        return {
            "answer": answer_text,
            "sources": sources,
            "grounded": is_grounded
        }

    def generate_summary(
        self,
        db: Session,
        user: Optional[User],
        material_id: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Generate or retrieve structured summary for a material:
        Returns { id, materialId, generatedAt, keyConcepts: [...], sections: [{id, title, body, points}] }
        """
        # 1. Check if summary already exists
        if not force_refresh:
            existing = db.query(Summary).filter(Summary.material_id == material_id).order_by(Summary.id.desc()).first()
            if existing and existing.sections_json:
                mat = db.query(Material).filter(Material.id == material_id).first()
                return {
                    "id": str(existing.id),
                    "materialId": material_id,
                    "materialTitle": mat.title if mat else material_id,
                    "generatedAt": existing.generated_at_str or "Recently",
                    "keyConcepts": existing.key_concepts_json or [],
                    "sections": existing.sections_json or []
                }

        # 2. Retrieve material and its content chunks
        mat = db.query(Material).filter(Material.id == material_id).first()
        if not mat:
            raise ValueError(f"Material '{material_id}' not found.")

        chunks = db.query(DocumentChunk).filter(DocumentChunk.material_id == material_id).order_by(DocumentChunk.chunk_index).all()
        if chunks:
            # Combine content from chunks (up to ~12000 chars for prompt)
            combined_text = "\n\n".join([f"[Page {c.page_number}]: {c.content}" for c in chunks[:25]])
        else:
            combined_text = f"Title: {mat.title}\nDescription: {mat.description}\nTopics: " + ", ".join([t.get("name", "") for t in (mat.topics_json or [])])

        # 3. Call Gemini to create structured JSON summary
        key_concepts = []
        sections = []

        if ai_service.is_configured() and ai_service.client:
            prompt = (
                f"You are an academic curriculum specialist. Generate an in-depth structured study summary of the following document:\n\n"
                f"Document Title: {mat.title}\n"
                f"Document Content:\n{combined_text[:12000]}\n\n"
                f"Generate a detailed summary formatted strictly as JSON with this schema:\n"
                f"{{\n"
                f'  "keyConcepts": ["Concept 1", "Concept 2", "Concept 3", "Concept 4", "Concept 5"],\n'
                f'  "sections": [\n'
                f'    {{\n'
                f'      "id": "s1",\n'
                f'      "title": "Section Title",\n'
                f'      "body": "Comprehensive explanation of this topic, theoretical foundation, and key equations or principles.",\n'
                f'      "points": [\n'
                f'        "High-yield bullet point 1",\n'
                f'        "High-yield bullet point 2",\n'
                f'        "High-yield bullet point 3"\n'
                f'      ]\n'
                f'    }}\n'
                f'  ]\n'
                f"}}"
            )
            try:
                from google.genai import types
                cfg = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    system_instruction="You are an expert study summarizer. Produce rich, structured, accurate academic summaries in JSON."
                )
                res = ai_service.client.models.generate_content(
                    model=ai_service.model_name,
                    contents=prompt,
                    config=cfg
                )
                parsed = json.loads(res.text)
                key_concepts = parsed.get("keyConcepts", [])
                raw_sections = parsed.get("sections", [])
                for i, sec in enumerate(raw_sections):
                    sections.append({
                        "id": sec.get("id") or f"s{i+1}",
                        "title": sec.get("title", f"Section {i+1}"),
                        "body": sec.get("body", ""),
                        "points": sec.get("points", [])
                    })
            except Exception as e:
                logger.error(f"Error generating structured summary with Gemini: {e}")

        # Fallback if Gemini unavailable or returned empty
        if not sections:
            key_concepts = [f"{mat.title} Overview", "Key Principles", "Methodologies", "Best Practices"]
            sections = [
                {
                    "id": "s1",
                    "title": f"Introduction to {mat.title}",
                    "body": mat.description or f"Comprehensive overview and foundational study notes for {mat.title}.",
                    "points": [
                        f"Fundamental scope and definitions of {mat.title}.",
                        "Core mechanisms and theoretical underpinnings.",
                        "Standard examination focus areas and application principles."
                    ]
                },
                {
                    "id": "s2",
                    "title": "Core Concepts & Architecture",
                    "body": "Detailed breakdown of the primary components, operations, and analytical rules established in this unit.",
                    "points": [
                        "Component separation and logical relationships.",
                        "Algorithmic and operational constraints.",
                        "Trade-offs in execution time, memory, and performance."
                    ]
                }
            ]

        # 4. Save to database
        summary_record = Summary(
            material_id=material_id,
            user_id=user.id if user else None,
            title=f"Summary of {mat.title}",
            generated_at_str="Generated today",
            key_concepts_json=key_concepts,
            sections_json=sections
        )
        db.add(summary_record)
        db.commit()
        db.refresh(summary_record)

        return {
            "id": str(summary_record.id),
            "materialId": material_id,
            "materialTitle": mat.title,
            "generatedAt": summary_record.generated_at_str,
            "keyConcepts": key_concepts,
            "sections": sections
        }

    def delete_material_index(self, db: Session, material_id: str):
        """
        Purge all vector chunk embeddings, summaries, and source references for a material.
        Ensures deleted materials leave no orphaned vector embeddings or citations.
        """
        try:
            db.query(SourceReference).filter(SourceReference.material_id == material_id).delete(synchronize_session=False)
            db.query(DocumentChunk).filter(DocumentChunk.material_id == material_id).delete(synchronize_session=False)
            db.query(Summary).filter(Summary.material_id == material_id).delete(synchronize_session=False)
            db.query(TutorInteraction).filter(TutorInteraction.material_id == material_id).delete(synchronize_session=False)
            logger.info(f"Purged all vector chunks, summaries, and tutor references for material '{material_id}'.")
        except Exception as e:
            logger.warning(f"Error during RAG cleanup for material '{material_id}': {e}")
            raise

rag_service = RAGService()
