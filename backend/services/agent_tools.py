"""
Voice Agent Tools for LiveKit Integration
"""
import asyncio
from typing import Dict, Any, List
from livekit.agents.llm import function_tool
import httpx
import os
from datetime import datetime

from services.chromadb_service import ChromaDBService
from services.database_service import DatabaseService
from services.tavily_service import TavilyService
from models import get_db


class VoiceAgentTools:
    """Collection of tools available to voice agents"""
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        self.chromadb_service = ChromaDBService()
        self.tavily_service = TavilyService()
    
    @function_tool(description="Search the company's knowledge base for information")
    async def query_knowledge_base(self, query: str) -> str:
        """Query the company's knowledge base for relevant information
        
        Args:
            query: The question or topic to search for
            
        Returns:
            Relevant information from the knowledge base
        """
        try:
            # Search in the agent's knowledge collection
            results = self.chromadb_service.query_documents(
                collection_name=f"agent_{self.agent_id}",
                query=query,
                n_results=3
            )
            
            if results and results.get('documents'):
                # Combine the most relevant documents
                combined_info = "\n\n".join([
                    doc for doc in results['documents'][0] if doc
                ])
                return combined_info or "No relevant information found in our knowledge base."
            else:
                return "No relevant information found in our knowledge base."
                
        except Exception as e:
            return f"Sorry, I encountered an error searching our knowledge base: {str(e)}"
    
    @function_tool(description="Get current business hours and contact information")
    async def get_business_info(self) -> str:
        """Get business hours, contact information, and location details
        
        Returns:
            Current business information
        """
        try:
            # Get agent details from database
            from sqlalchemy.orm import Session
            db = next(get_db())
            
            agent = DatabaseService.get_agent(db, self.agent_id)
            if not agent:
                return "Sorry, I couldn't retrieve our business information right now."
            
            # Extract business info from agent's configuration
            business_info = []
            
            if hasattr(agent, 'company_name') and agent.company_name:
                business_info.append(f"Company: {agent.company_name}")
            
            if hasattr(agent, 'business_type') and agent.business_type:
                business_info.append(f"Business Type: {agent.business_type}")
            
            # Add standard business hours (can be customized per agent)
            business_info.extend([
                "Business Hours: Monday to Friday, 9 AM to 6 PM",
                "Phone: Available through this voice assistant",
                "Email: Contact us through our website",
                "We're here to help with all your inquiries!"
            ])
            
            return "\n".join(business_info)
            
        except Exception as e:
            return "Sorry, I couldn't retrieve our business information right now. Please try again."
    
    @function_tool(description="Capture lead information from interested customers")
    async def capture_lead(self, name: str, email: str, phone: str = "", interest: str = "") -> str:
        """Capture lead information for follow-up
        
        Args:
            name: Customer's name
            email: Customer's email address
            phone: Customer's phone number (optional)
            interest: What the customer is interested in (optional)
            
        Returns:
            Confirmation message
        """
        try:
            # Here you would typically save to your CRM or database
            lead_data = {
                "agent_id": self.agent_id,
                "name": name,
                "email": email,
                "phone": phone,
                "interest": interest,
                "captured_at": datetime.utcnow().isoformat(),
                "source": "voice_agent"
            }
            
            # TODO: Integrate with your CRM system
            # For now, we'll log it (in production, save to database/CRM)
            print(f"Lead captured: {lead_data}")
            
            return f"Thank you {name}! I've captured your information. Someone from our team will reach out to you soon regarding {interest if interest else 'your inquiry'}."
            
        except Exception as e:
            return "Sorry, I had trouble saving your information. Could you please try again or contact us directly?"
    
    @function_tool(description="Search for current information on the web")
    async def web_search(self, query: str) -> str:
        """Search the web for current information
        
        Args:
            query: What to search for
            
        Returns:
            Current information from the web
        """
        try:
            results = await self.tavily_service.search(query, max_results=2)
            
            if results:
                # Format the results for voice response
                formatted_results = []
                for result in results[:2]:  # Limit to top 2 results
                    title = result.get('title', 'No title')
                    content = result.get('content', 'No content available')
                    # Truncate content for voice response
                    content = content[:200] + "..." if len(content) > 200 else content
                    formatted_results.append(f"{title}: {content}")
                
                return "Here's what I found: " + " | ".join(formatted_results)
            else:
                return "I couldn't find current information about that topic. Let me help you with something else."
                
        except Exception as e:
            return "Sorry, I couldn't search for that information right now. Is there something else I can help you with?"
    
    @function_tool(description="Transfer the conversation to a human agent")
    async def transfer_to_human(self, reason: str = "Customer requested human assistance") -> str:
        """Transfer the conversation to a human agent
        
        Args:
            reason: Reason for the transfer
            
        Returns:
            Transfer confirmation message
        """
        try:
            # In a real implementation, this would trigger your call center system
            transfer_data = {
                "agent_id": self.agent_id,
                "transfer_reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # TODO: Integrate with your call center or support system
            print(f"Transfer requested: {transfer_data}")
            
            return f"I'm connecting you with one of our human representatives now. They'll be able to assist you with {reason.lower()}. Please hold on for just a moment."
            
        except Exception as e:
            return "I'm having trouble connecting you right now. Please try calling our main number or visiting our website for immediate assistance."
    
    @function_tool(description="Check appointment availability and schedule meetings")
    async def schedule_appointment(self, preferred_date: str, preferred_time: str, service_type: str = "", customer_name: str = "") -> str:
        """Schedule an appointment for the customer
        
        Args:
            preferred_date: Customer's preferred date (e.g., "tomorrow", "next Monday", "March 15")
            preferred_time: Customer's preferred time (e.g., "2 PM", "morning", "afternoon")
            service_type: Type of service or meeting (optional)
            customer_name: Customer's name (optional)
            
        Returns:
            Appointment scheduling confirmation or next steps
        """
        try:
            # In a real implementation, this would check your calendar system
            appointment_data = {
                "agent_id": self.agent_id,
                "preferred_date": preferred_date,
                "preferred_time": preferred_time,
                "service_type": service_type,
                "customer_name": customer_name,
                "requested_at": datetime.utcnow().isoformat()
            }
            
            # TODO: Integrate with your calendar/booking system
            print(f"Appointment requested: {appointment_data}")
            
            if customer_name:
                return f"Great {customer_name}! I'm checking our availability for {preferred_date} around {preferred_time} for {service_type if service_type else 'your appointment'}. Let me connect you with someone who can confirm the exact time and details."
            else:
                return f"I'd be happy to help you schedule an appointment for {preferred_date} around {preferred_time}. Let me connect you with our scheduling team to confirm availability and get your details."
                
        except Exception as e:
            return "I'm having trouble accessing our scheduling system right now. Please try calling us directly or visiting our website to book an appointment."


def get_agent_tools(agent_id: int) -> List:
    """Get all available tools for a specific agent
    
    Args:
        agent_id: The ID of the agent
        
    Returns:
        List of tool functions
    """
    tools = VoiceAgentTools(agent_id)
    
    return [
        tools.query_knowledge_base,
        tools.get_business_info,
        tools.capture_lead,
        tools.web_search,
        tools.transfer_to_human,
        tools.schedule_appointment
    ]