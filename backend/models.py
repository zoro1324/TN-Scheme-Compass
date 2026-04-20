import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from backend.database import Base


class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(String(64), unique=True, nullable=False, index=True)
    scheme_name = Column(String(512), nullable=False, index=True)
    scheme_level = Column(String(64), nullable=True)
    administering_body = Column(String(512), nullable=True)
    target_beneficiaries = Column(Text, nullable=True)
    eligibility_criteria = Column(Text, nullable=True)
    income_limit = Column(Text, nullable=True)
    age_range = Column(Text, nullable=True)
    benefit_description = Column(Text, nullable=True)
    benefit_amount = Column(String(256), nullable=True)
    application_process = Column(Text, nullable=True)
    required_documents = Column(Text, nullable=True)
    application_url = Column(Text, nullable=True)
    tamil_nadu_relevance_reason = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    source_domain = Column(String(256), nullable=True)
    evidence_snippet = Column(Text, nullable=True)
    extraction_method = Column(String(128), nullable=True)
    confidence = Column(Float, nullable=True)
    last_verified_on = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="session", uselist=False, cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(24), nullable=False)
    content = Column(Text, nullable=False)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("ChatSession", back_populates="messages")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    session_id = Column(String(64), ForeignKey("chat_sessions.id", ondelete="CASCADE"), primary_key=True)
    profile_json = Column(Text, nullable=False, default="{}")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    session = relationship("ChatSession", back_populates="profile")
