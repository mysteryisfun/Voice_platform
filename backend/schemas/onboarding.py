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


# Enhanced onboarding configuration schemas
class AgentIdentityConfig(BaseModel):
    """Agent identity and role configuration"""
    agent_name: str = Field(..., description="Custom agent name")
    agent_role: str = Field(..., description="Agent role/title")
    greeting_message: Optional[str] = Field(None, description="Custom greeting message")


class VoiceConfig(BaseModel):
    """Voice and personality configuration"""
    voice_id: str = Field(..., description="Selected voice ID")
    personality: str = Field(..., description="Agent personality")
    tone: str = Field(..., description="Speaking tone")
    speaking_speed: str = Field(default="normal", description="Speaking speed")
    response_style: str = Field(default="balanced", description="Response length style")


class ToolsConfig(BaseModel):
    """Tools and escalation configuration"""
    enabled_tools: List[str] = Field(..., description="List of enabled tool names")
    escalation_triggers: List[str] = Field(default=[], description="Escalation conditions")
    special_instructions: Optional[str] = Field(None, description="Special instructions")


class OnboardingConfigRequest(BaseModel):
    """Request to configure agent with enhanced settings"""
    session_id: str = Field(..., description="Session identifier")
    identity_config: AgentIdentityConfig
    voice_config: VoiceConfig
    tools_config: ToolsConfig


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
    configuration: OnboardingConfigRequest = Field(..., description="Final agent configuration")


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


# Available voice options
class VoiceOption(BaseModel):
    """Available voice option"""
    id: str = Field(..., description="Voice identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Voice description")
    sample_url: Optional[str] = Field(None, description="Sample audio URL")


class AvailableToolOption(BaseModel):
    """Available tool option"""
    id: str = Field(..., description="Tool identifier")
    name: str = Field(..., description="Tool display name")
    description: str = Field(..., description="Tool description")
    category: str = Field(..., description="Tool category")
    required: bool = Field(default=False, description="Whether tool is required")