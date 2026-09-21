from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(String(100), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False, default=0)
    page_number = Column(Integer, nullable=False, default=1)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    embedding_json = Column(JSON, nullable=True)  # Float array (e.g. 3072-dim vector)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    material = relationship("Material", back_populates="chunks")

class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(String(100), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=True)
    generated_at_str = Column(String(100), default="Just now", nullable=False)
    key_concepts_json = Column(JSON, default=list, nullable=False)  # ['concept1', 'concept2', ...]
    sections_json = Column(JSON, default=list, nullable=False)      # [{id, title, body, points: [...]}]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    material = relationship("Material", back_populates="summaries")
    user = relationship("User")

class TutorInteraction(Base):
    __tablename__ = "tutor_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(String(100), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    grounded = Column(Boolean, default=True, nullable=False)
    sources_json = Column(JSON, default=list, nullable=False)  # [{label: '...', page: 'Page X'}]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="tutor_interactions")
    material = relationship("Material", back_populates="tutor_interactions")
    sources = relationship("SourceReference", back_populates="interaction", cascade="all, delete-orphan")

class SourceReference(Base):
    __tablename__ = "source_references"

    id = Column(Integer, primary_key=True, index=True)
    tutor_interaction_id = Column(Integer, ForeignKey("tutor_interactions.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(String(100), ForeignKey("materials.id", ondelete="CASCADE"), nullable=True, index=True)
    chunk_id = Column(Integer, ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True)
    label = Column(String(255), nullable=False)
    page = Column(String(50), nullable=True)
    page_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    interaction = relationship("TutorInteraction", back_populates="sources")
    material = relationship("Material")
    chunk = relationship("DocumentChunk")

