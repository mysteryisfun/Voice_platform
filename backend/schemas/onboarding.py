"""
Pydantic schemas for onboarding endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class OnboardingStartRequest(BaseModel):
    """Request to start onboarding session"""
    initial_context: Optional[str] = Field(None, description="Initial context or information about the business")


class OnboardingStartResponse(BaseModel):
    """Response when starting onboarding session"""
    session_id: str = Field(..., description="Unique session identifier")
    agent_id: int = Field(..., description="Created agent ID")
    first_question: str = Field(..., description="First AI-generated question")
    status: str = Field(..., description="Session status")


class OnboardingAnswerRequest(BaseModel):
    """Request to submit an answer"""
    session_id: str = Field(..., description="Session identifier")
    question_number: int = Field(..., description="Current question number")
    answer: str = Field(..., description="User's answer to the question")


class OnboardingAnswerResponse(BaseModel):
    """Response after submitting an answer"""
    session_id: str = Field(..., description="Session identifier")
    next_question: Optional[str] = Field(None, description="Next AI-generated question")
    is_complete: bool = Field(..., description="Whether the interview is complete")
    progress: str = Field(..., description="Progress indicator (e.g., '3/8')")
    total_questions: int = Field(..., description="Total questions asked so far")


class OnboardingStatusResponse(BaseModel):
    """Response for onboarding status check"""
    session_id: str = Field(..., description="Session identifier")
    agent_id: int = Field(..., description="Agent ID")
    status: str = Field(..., description="Overall session status")
    current_question_number: int = Field(..., description="Current question number")
    total_questions_asked: int = Field(..., description="Total questions asked")
    web_scraping_status: str = Field(..., description="Web scraping status")
    document_processing_status: str = Field(..., description="Document processing status")
    vector_embedding_status: str = Field(..., description="Vector embedding status")
    progress_percentage: int = Field(..., description="Overall progress as percentage")


class OnboardingCompleteRequest(BaseModel):
    """Request to complete onboarding"""
    session_id: str = Field(..., description="Session identifier")


class OnboardingCompleteResponse(BaseModel):
    """Response when onboarding is completed"""
    agent_id: int = Field(..., description="Completed agent ID")
    agent_name: str = Field(..., description="Generated agent name")
    status: str = Field(..., description="Agent status")
    system_prompt: str = Field(..., description="Generated system prompt")
    knowledge_chunks_count: int = Field(..., description="Number of knowledge chunks created")
    message: str = Field(..., description="Success message")


class QuestionAndAnswer(BaseModel):
    """Individual Q&A pair"""
    question: str = Field(..., description="The question asked")
    answer: str = Field(..., description="The answer provided")
    timestamp: str = Field(..., description="When the answer was submitted")
    question_number: int = Field(..., description="Sequential question number")