"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class OnboardingStartRequest(BaseModel):
    """Request to start onboarding process"""
    initial_context: Optional[str] = Field(None, description="Any initial context about the business")


class OnboardingStartResponse(BaseModel):
    """Response when starting onboarding"""
    session_id: str = Field(description="Unique session identifier")
    agent_id: int = Field(description="Created agent ID")
    first_question: str = Field(description="First AI-generated question")
    status: str = Field(description="Session status")


class OnboardingAnswerRequest(BaseModel):
    """Request to submit an answer and get next question"""
    session_id: str = Field(description="Session identifier")
    answer: str = Field(description="User's answer to current question")
    question_number: int = Field(description="Current question number")


class OnboardingAnswerResponse(BaseModel):
    """Response with next question or completion"""
    session_id: str
    next_question: Optional[str] = Field(None, description="Next question if not complete")
    is_complete: bool = Field(description="Whether onboarding is finished")
    progress: str = Field(description="Progress indicator like '3/8'")
    total_questions: int = Field(description="Total questions asked so far")


class OnboardingStatusResponse(BaseModel):
    """Status of onboarding session"""
    session_id: str
    agent_id: int
    status: str = Field(description="Session status: started, in_progress, processing_data, completed, failed")
    current_question_number: int
    total_questions_asked: int
    web_scraping_status: str = Field(description="pending, in_progress, completed, failed")
    document_processing_status: str = Field(description="pending, in_progress, completed, failed")
    vector_embedding_status: str = Field(description="pending, in_progress, completed, failed")
    progress_percentage: int = Field(description="Overall completion percentage")


class OnboardingCompleteRequest(BaseModel):
    """Request to finalize agent creation"""
    session_id: str
    website_url: Optional[str] = Field(None, description="Business website URL")


class OnboardingCompleteResponse(BaseModel):
    """Response when onboarding is completed"""
    agent_id: int
    agent_name: str
    status: str
    system_prompt: str = Field(description="Generated system prompt for the agent")
    knowledge_chunks_count: int = Field(description="Number of knowledge chunks created")
    message: str


class QuestionAndAnswer(BaseModel):
    """Individual Q&A pair"""
    question: str
    answer: str
    timestamp: datetime
    question_number: int


class AgentResponse(BaseModel):
    """Agent information response"""
    id: int
    name: Optional[str]
    description: Optional[str]
    company_name: Optional[str]
    industry: Optional[str]
    website_url: Optional[str]
    personality: str
    tone: str
    language: str
    status: str
    created_at: datetime
    deployed_at: Optional[datetime]


class AgentListResponse(BaseModel):
    """List of agents response"""
    agents: List[AgentResponse]
    total: int
    message: str


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
