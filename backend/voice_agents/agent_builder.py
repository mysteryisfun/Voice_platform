"""
Meta agent that builds complete voice agents from onboarding data.

This module contains the AgentBuilder class that takes information
from the onboarding process and creates complete, configured voice agents
by filling prompt templates and setting up tools.
"""

import json
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from .prompts import get_meta_agent_prompt, AgentPromptComponents
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class VoiceAgentBuilder:
    """Meta agent that builds voice agent configurations from onboarding data."""
    
    def __init__(self):
        """Initialize the meta agent with OpenAI model."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,  # Low temperature for consistent, professional output
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.meta_prompt = get_meta_agent_prompt()
    
    async def build_agent_configuration(self, onboarding_data: Dict[str, Any]) -> AgentPromptComponents:
        """
        Build complete agent configuration from onboarding data.
        
        Args:
            onboarding_data: Dictionary containing all onboarding information
            
        Returns:
            AgentPromptComponents: Structured agent configuration
        """
        try:
            logger.info(f"Building agent configuration for: {onboarding_data.get('agent_name', 'Unknown')}")
            
            # Format the onboarding data for the meta agent
            formatted_data = self._format_onboarding_data(onboarding_data)
            
            # Generate the prompt with onboarding data
            messages = self.meta_prompt.format_messages(**formatted_data)
            
            # Get response from meta agent
            response = await self.llm.ainvoke(messages)
            
            # Parse the JSON response
            agent_config_json = response.content.strip()
            if agent_config_json.startswith("```json"):
                agent_config_json = agent_config_json.replace("```json", "").replace("```", "").strip()
            
            agent_config_dict = json.loads(agent_config_json)
            
            # Create and validate the AgentPromptComponents
            agent_components = AgentPromptComponents(**agent_config_dict)
            
            logger.info(f"Successfully built agent configuration for: {agent_components.agent_name}")
            return agent_components
            
        except Exception as e:
            logger.error(f"Error building agent configuration: {str(e)}")
            raise Exception(f"Failed to build agent configuration: {str(e)}")
    
    def _format_onboarding_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Format onboarding data for the meta agent prompt."""
        
        # Extract basic agent information
        agent_name = data.get('agent_name', 'Assistant')
        company_name = data.get('company_name', data.get('business_type', 'Your Business'))
        business_type = data.get('business_type', 'General Business')
        agent_role = data.get('agent_role', 'Customer Service Representative')
        voice_id = data.get('voice_id', 'alloy')
        speaking_speed = data.get('speaking_speed', 'normal')
        
        # Extract Q&A session data
        qa_history = data.get('qa_history', [])
        services_info = self._extract_qa_info(qa_history, 'service', 'products', 'business')
        target_customers = self._extract_qa_info(qa_history, 'customer', 'client', 'audience')
        business_hours_info = self._extract_qa_info(qa_history, 'hour', 'time', 'availability')
        business_purpose = self._extract_qa_info(qa_history, 'purpose', 'goal', 'mission')
        tone_preference = data.get('tone_preference', 'professional and friendly')
        
        # Format enabled tools
        enabled_tools = data.get('enabled_tools', [])
        tools_description = self._format_tools_description(enabled_tools)
        
        # Extract knowledge summary
        knowledge_summary = data.get('knowledge_summary', 'General business knowledge from uploaded documents and website information')
        
        # Other configurations
        special_instructions = data.get('special_instructions', 'Provide excellent customer service')
        escalation_triggers = data.get('escalation_triggers', 'Complex technical issues, billing disputes, or customer complaints')
        
        return {
            'agent_name': agent_name,
            'company_name': company_name,
            'business_type': business_type,
            'agent_role': agent_role,
            'voice_id': voice_id,
            'speaking_speed': speaking_speed,
            'services_info': services_info,
            'target_customers': target_customers,
            'business_hours_info': business_hours_info,
            'business_purpose': business_purpose,
            'tone_preference': tone_preference,
            'enabled_tools': tools_description,
            'knowledge_summary': knowledge_summary,
            'special_instructions': special_instructions,
            'escalation_triggers': escalation_triggers
        }
    
    def _extract_qa_info(self, qa_history: list, *keywords: str) -> str:
        """Extract relevant information from Q&A history based on keywords."""
        relevant_info = []
        
        for qa in qa_history:
            question = qa.get('question', '').lower()
            answer = qa.get('answer', '')
            
            # Check if any keyword appears in the question
            if any(keyword in question for keyword in keywords):
                relevant_info.append(answer)
        
        return '. '.join(relevant_info) if relevant_info else f'Information not provided during onboarding'
    
    def _format_tools_description(self, enabled_tools: list) -> str:
        """Format enabled tools into a description for the meta agent."""
        if not enabled_tools:
            return "Basic knowledge base queries only"
        
        tool_descriptions = {
            'knowledge_base': 'Search company knowledge base and documents',
            'lead_capture': 'Collect visitor contact information and requirements',
            'appointment_booking': 'Schedule meetings and consultations',
            'contact_info': 'Provide business contact information and hours',
            'gmail_integration': 'Send emails and manage email communication',
            'google_calendar': 'Check availability and schedule appointments in Google Calendar',
            'human_transfer': 'Escalate to human representatives when needed'
        }
        
        descriptions = []
        for tool in enabled_tools:
            if tool in tool_descriptions:
                descriptions.append(f"- {tool_descriptions[tool]}")
        
        return '\n'.join(descriptions)

# Global instance
agent_builder = VoiceAgentBuilder()
