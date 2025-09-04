"""
Simple completion request schema for frontend compatibility
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class SimpleCompleteRequest(BaseModel):
    """Simple completion request matching frontend structure"""
    agent_name: str = Field(..., description="Agent name")
    business_type: str = Field(..., description="Business type")
    agent_role: str = Field(..., description="Agent role")
    voice_id: str = Field(..., description="Voice ID")
    voice_name: Optional[str] = Field(None, description="Voice name")
    enabled_tools: List[str] = Field(default_factory=list, description="Enabled tools")
    session_id: str = Field(..., description="Session ID")
