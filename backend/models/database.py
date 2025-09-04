"""
Database models for Voice Agent Platform
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class AgentStatus(str, Enum):
    """Agent deployment status"""
    CREATED = "created"
    PROCESSING = "processing"
    DEPLOYED = "deployed"
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"


class OnboardingStatus(str, Enum):
    """Onboarding session status"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    PROCESSING_DATA = "processing_data"
    COMPLETED = "completed"
    FAILED = "failed"


class Agent(Base):
    """Voice agent configuration and metadata"""
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)  # Allow null during onboarding
    description = Column(Text)
    
    # Business information
    company_name = Column(String(255), nullable=True)  # Allow null during onboarding
    industry = Column(String(100))
    website_url = Column(String(500))
    
    # Agent configuration
    personality = Column(String(50), default="professional")  # professional, friendly, casual, technical
    tone = Column(String(50), default="helpful")
    language = Column(String(10), default="en")
    response_style = Column(String(50), default="balanced")  # concise, detailed, balanced
    
    # System configuration
    system_prompt = Column(Text)
    status = Column(String(20), default=AgentStatus.CREATED)
    livekit_room_id = Column(String(255))
    widget_config = Column(JSON)  # Widget styling and configuration
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deployed_at = Column(DateTime)
    
    # Relationships
    onboarding_session = relationship("OnboardingSession", back_populates="agent", uselist=False)
    leads = relationship("Lead", back_populates="agent")
    appointments = relationship("Appointment", back_populates="agent")
    knowledge_chunks = relationship("KnowledgeChunk", back_populates="agent")


class OnboardingSession(Base):
    """Onboarding session tracking and Q&A history"""
    __tablename__ = "onboarding_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), unique=True)
    
    # Session management
    status = Column(String(20), default=OnboardingStatus.STARTED)
    current_question_number = Column(Integer, default=1)
    total_questions_asked = Column(Integer, default=0)
    
    # Business data collection
    website_url = Column(String(500))
    uploaded_documents = Column(JSON)  # List of uploaded PDF file paths
    
    # Q&A history
    questions_and_answers = Column(JSON)  # [{question: str, answer: str, timestamp: str}]
    current_question = Column(Text)  # Store the current pending question
    
    # Processing status
    web_scraping_status = Column(String(20), default="pending")  # pending, in_progress, completed, failed
    document_processing_status = Column(String(20), default="pending")
    vector_embedding_status = Column(String(20), default="pending")
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime)
    
    # Relationships
    agent = relationship("Agent", back_populates="onboarding_session")


class Lead(Base):
    """Customer leads captured by voice agents"""
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    # Lead information
    name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    company = Column(String(255))
    
    # Interaction details
    requirements = Column(Text)
    conversation_summary = Column(Text)
    lead_score = Column(Float, default=0.0)  # 0-100 scoring
    
    # Session information
    livekit_session_id = Column(String(255))
    conversation_duration = Column(Integer)  # seconds
    
    # Metadata
    captured_at = Column(DateTime, default=func.now())
    followed_up_at = Column(DateTime)
    
    # Relationships
    agent = relationship("Agent", back_populates="leads")


class Appointment(Base):
    """Scheduled appointments through voice agents"""
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    # Appointment details
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_phone = Column(String(50))
    
    # Scheduling
    scheduled_datetime = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    meeting_type = Column(String(50))  # consultation, demo, support, etc.
    
    # Meeting details
    agenda = Column(Text)
    meeting_link = Column(String(500))  # Zoom, Teams, etc.
    calendar_event_id = Column(String(255))  # External calendar system ID
    
    # Status tracking
    status = Column(String(20), default="scheduled")  # scheduled, confirmed, completed, cancelled, no_show
    confirmation_sent = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    
    # Session information
    livekit_session_id = Column(String(255))
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="appointments")


class KnowledgeChunk(Base):
    """Vector embeddings and knowledge base chunks for each agent"""
    __tablename__ = "knowledge_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    # Content information
    content = Column(Text, nullable=False)
    content_type = Column(String(50))  # website, pdf, manual
    source_url = Column(String(500))  # Original source
    source_file = Column(String(255))  # File path if from document
    
    # Vector information (metadata only, actual vectors in ChromaDB)
    chunk_index = Column(Integer)  # Order within source document
    chunk_id = Column(String(255), unique=True)  # ChromaDB document ID
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="knowledge_chunks")


class ConversationSession(Base):
    """Voice conversation sessions for analytics"""
    __tablename__ = "conversation_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    # Session details
    livekit_session_id = Column(String(255), unique=True, nullable=False)
    livekit_room_id = Column(String(255))
    
    # Analytics
    duration_seconds = Column(Integer)
    message_count = Column(Integer, default=0)
    user_satisfaction = Column(Float)  # 1-5 rating if collected
    
    # Outcomes
    lead_captured = Column(Boolean, default=False)
    appointment_booked = Column(Boolean, default=False)
    issue_resolved = Column(Boolean)
    
    # Session metadata
    user_ip = Column(String(45))  # IPv4/IPv6
    user_agent = Column(String(500))
    referrer_url = Column(String(500))
    
    # Timestamps
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime)
    
    # Relationships - Note: Not direct FK to maintain flexibility
    # agent = relationship("Agent")
