"""
Tool definitions and implementations for voice agents.

This module contains all the tools that voice agents can use,
including Gmail, Calendar, Sheets integration via n8n webhooks,
and local tools like product showcase.
"""

import json
import aiohttp
import asyncio
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging
from livekit.agents.llm import function_tool
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# n8n Webhook Configuration
N8N_WEBHOOK_URL = "https://whatever12454.app.n8n.cloud/webhook-test/26ba121c-38e1-4e77-aa04-0a3ffbf0026a"

# ===============================
# BASE CLASSES & UTILITIES
# ===============================

class ToolResponse(BaseModel):
    success: bool
    message: str
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

# Webhook client for n8n integration
async def call_n8n_webhook(payload: Dict[str, Any]) -> ToolResponse:
    """Call n8n webhook with the given payload"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                N8N_WEBHOOK_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.text()
                    return ToolResponse(
                        success=True,
                        message=result if result else "Operation completed successfully",
                        data={"status_code": response.status}
                    )
                else:
                    error_msg = f"HTTP {response.status}: {await response.text()}"
                    return ToolResponse(success=False, message="", error=error_msg)
    except Exception as e:
        logger.error(f"n8n webhook call failed: {str(e)}")
        return ToolResponse(success=False, message="", error=str(e))

# ===============================
# GMAIL TOOLS
# ===============================

@function_tool
async def send_email(agent_id: int, to: str, subject: str, body: str, template: str = None) -> str:
    """Send email via Gmail integration
    
    Args:
        agent_id: ID of the agent sending the email
        to: Recipient email address
        subject: Email subject line
        body: Email body content
        template: Optional email template to use
        
    Returns:
        Status message indicating success or failure
    """
    payload = {
        "tool": "gmail",
        "action": "send_email",
        "agent_id": agent_id,
        "parameters": {
            "to": to,
            "subject": subject,
            "body": body,
            "template": template
        }
    }
    result = await call_n8n_webhook(payload)
    return result.message if result.success else f"Failed to send email: {result.error}"

@function_tool
async def get_recent_emails(agent_id: int, customer_email: str, limit: int = 5, days_back: int = 30) -> str:
    """Get recent emails for a customer via Gmail integration
    
    Args:
        agent_id: ID of the agent requesting emails
        customer_email: Email address to search for conversations
        limit: Maximum number of emails to retrieve (default: 5)
        days_back: Number of days back to search (default: 30)
        
    Returns:
        Summary of recent emails or error message
    """
    payload = {
        "tool": "gmail",
        "action": "get_recent_emails",
        "agent_id": agent_id,
        "parameters": {
            "customer_email": customer_email,
            "limit": limit,
            "days_back": days_back
        }
    }
    result = await call_n8n_webhook(payload)
    return result.message if result.success else f"Failed to get emails: {result.error}"

# ===============================
# CALENDAR TOOLS
# ===============================

@function_tool
async def check_availability(agent_id: int, date_range: str, duration_minutes: int = 30, time_preference: str = None) -> str:
    """Check calendar availability via Calendar integration
    
    Args:
        agent_id: ID of the agent checking availability
        date_range: Date range to check (e.g., "2023-12-01 to 2023-12-05")
        duration_minutes: Required meeting duration in minutes (default: 30)
        time_preference: Preferred time of day (e.g., "morning", "afternoon")
        
    Returns:
        Available time slots or message if no availability
    """
    payload = {
        "tool": "calendar",
        "action": "check_availability",
        "agent_id": agent_id,
        "parameters": {
            "date_range": date_range,
            "duration_minutes": duration_minutes,
            "time_preference": time_preference
        }
    }
    result = await call_n8n_webhook(payload)
    return result.message if result.success else f"Failed to check availability: {result.error}"

@function_tool
async def get_events(agent_id: int, date_range: str = None, customer_email: str = None, limit: int = 10) -> str:
    """Get calendar events - needed to get event IDs for update/delete operations
    
    Args:
        agent_id: ID of the agent requesting events
        date_range: Optional date range filter (e.g., "2023-12-01 to 2023-12-05")
        customer_email: Optional email filter for specific customer events
        limit: Maximum number of events to retrieve (default: 10)
        
    Returns:
        List of calendar events with their IDs and details
    """
    payload = {
        "tool": "calendar",
        "action": "get_events",
        "agent_id": agent_id,
        "parameters": {
            "date_range": date_range,
            "customer_email": customer_email,
            "limit": limit
        }
    }
    result = await call_n8n_webhook(payload)
    return result.message if result.success else f"Failed to get events: {result.error}"

@function_tool
async def book_appointment(agent_id: int, customer_name: str, customer_email: str, 
                          date: str, time: str, duration_minutes: int = 30, 
                          description: str = None, location: str = None) -> str:
    """Book a new appointment via Calendar integration
    
    Args:
        agent_id: ID of the agent booking the appointment
        customer_name: Name of the customer
        customer_email: Email address of the customer
        date: Date for the appointment (YYYY-MM-DD format)
        time: Time for the appointment (HH:MM format)
        duration_minutes: Duration of the appointment in minutes (default: 30)
        description: Optional description or notes for the appointment
        location: Optional meeting location or video link
        
    Returns:
        Confirmation with appointment details or error message
    """
    payload = {
        "tool": "calendar",
        "action": "book_appointment",
        "agent_id": agent_id,
        "parameters": {
            "customer_name": customer_name,
            "customer_email": customer_email,
            "date": date,
            "time": time,
            "duration_minutes": duration_minutes,
            "description": description,
            "location": location
        }
    }
    result = await call_n8n_webhook(payload)
    return result.message if result.success else f"Failed to book appointment: {result.error}"

@function_tool
async def update_event(agent_id: int, event_id: str, customer_name: str = None, 
                      customer_email: str = None, date: str = None, time: str = None,
                      duration_minutes: int = None, description: str = None, location: str = None) -> str:
    """Update an existing calendar event
    
    Args:
        agent_id: ID of the agent updating the event
        event_id: ID of the event to update (get from get_events)
        customer_name: Updated customer name (optional)
        customer_email: Updated customer email (optional)
        date: Updated date (YYYY-MM-DD format, optional)
        time: Updated time (HH:MM format, optional)
        duration_minutes: Updated duration in minutes (optional)
        description: Updated description (optional)
        location: Updated location (optional)
        
    Returns:
        Updated event details or error message
    """
    payload = {
        "tool": "calendar",
        "action": "update_event",
        "agent_id": agent_id,
        "parameters": {
            "event_id": event_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "date": date,
            "time": time,
            "duration_minutes": duration_minutes,
            "description": description,
            "location": location
        }
    }
    result = await call_n8n_webhook(payload)
    return result.message if result.success else f"Failed to update event: {result.error}"

@function_tool
async def delete_event(agent_id: int, event_id: str) -> str:
    """Delete a calendar event
    
    Args:
        agent_id: ID of the agent deleting the event
        event_id: ID of the event to delete (get from get_events)
        
    Returns:
        Confirmation of deletion or error message
    """
    payload = {
        "tool": "calendar",
        "action": "delete_event",
        "agent_id": agent_id,
        "parameters": {
            "event_id": event_id
        }
    }
    result = await call_n8n_webhook(payload)
    return result.message if result.success else f"Failed to delete event: {result.error}"

# ===============================
# SHEETS TOOLS (Lead Management)
# ===============================

@function_tool
async def append_or_update_lead(agent_id: int, name: str, date: str, time: str, 
                               email: str = None, query: str = None, 
                               phone: str = None, status: str = "new") -> str:
    """Append or update lead information in Google Sheets
    
    Args:
        agent_id: ID of the agent managing the lead
        name: Customer name
        date: Contact date (YYYY-MM-DD format)
        time: Contact time (HH:MM format)
        email: Customer email address (optional)
        query: Customer query or interest (optional)
        phone: Customer phone number (optional)
        status: Lead status (default: "new")
        
    Returns:
        Confirmation with lead details or error message
    """
    payload = {
        "tool": "sheets",
        "action": "append_or_update_lead",
        "agent_id": agent_id,
        "parameters": {
            "name": name,
            "date": date,
            "time": time,
            "email": email,
            "query": query,
            "phone": phone,
            "status": status
        }
    }
    result = await call_n8n_webhook(payload)
    return result.message if result.success else f"Failed to update lead: {result.error}"

@function_tool
async def get_lead_rows(agent_id: int, name: str) -> str:
    """Get lead information from Google Sheets by customer name
    
    Args:
        agent_id: ID of the agent requesting lead data
        name: Customer name to search for
        
    Returns:
        Lead information or message if not found
    """
    payload = {
        "tool": "sheets",
        "action": "get_lead_rows",
        "agent_id": agent_id,
        "parameters": {
            "name": name
        }
    }
    result = await call_n8n_webhook(payload)
    return result.message if result.success else f"Failed to get lead: {result.error}"

# ===============================
# HUMAN TRANSFER TOOL
# ===============================

@function_tool
async def escalate_to_human(agent_id: int, customer_name: str, customer_contact: str,
                           reason: str, context: str = None, priority: str = "normal") -> str:
    """Escalate the conversation to a human agent
    
    Args:
        agent_id: ID of the current agent
        customer_name: Name of the customer requesting escalation
        customer_contact: Customer's contact information (email or phone)
        reason: Reason for escalation (complex query, complaint, etc.)
        context: Optional conversation context for the human agent
        priority: Escalation priority (low, normal, high, urgent)
        
    Returns:
        Escalation confirmation and estimated wait time
    """
    # Get admin email from environment variables
    admin_email = os.getenv("ADMIN_MAIL", "admin@company.com")
    
    # Create detailed escalation email
    email_subject = f"🚨 Customer Escalation - {priority.upper()} Priority"
    
    email_body = f"""
CUSTOMER ESCALATION REQUEST

Customer Details:
- Name: {customer_name}
- Contact: {customer_contact}
- Priority: {priority.upper()}

Escalation Reason:
{reason}

Conversation Context:
{context if context else "No additional context provided"}

Agent Information:
- Agent ID: {agent_id}
- Escalation Time: {asyncio.get_event_loop().time()}

Please contact the customer as soon as possible to resolve their query.

---
This escalation was automatically generated by the Voice Agent Platform.
    """.strip()
    
    # Send email to admin using our send_email tool
    try:
        email_result = await send_email(
            agent_id=agent_id,
            to=admin_email,
            subject=email_subject,
            body=email_body,
            template=None
        )
        
        # Return confirmation message for the customer
        if "id" in email_result:  # Gmail returns message ID on success
            return f"Your request has been escalated to our human support team. An agent will contact you at {customer_contact} within the next 15-30 minutes. Reference ID: ESC-{agent_id}-{customer_name[:3].upper()}"
        else:
            return f"Your request has been escalated to our human support team. An agent will contact you at {customer_contact} shortly."
            
    except Exception as e:
        logger.error(f"Failed to send escalation email: {str(e)}")
        return f"Your escalation request has been received. Our team will contact you at {customer_contact} as soon as possible."

# ===============================
# PRODUCT SHOWCASE TOOL (Local)
# ===============================

# Import DuoLife product data
import sys
sys.path.append('.')
from duolife_products_data import DUOLIFE_PRODUCTS, get_product_recommendation, get_product_by_id, get_products_by_category

@function_tool
async def show_product(agent_id: int, customer_name: str, health_goals: str = None, 
                      budget_preference: str = "standard", specific_needs: str = None) -> str:
    """Show relevant DuoLife health products based on customer needs. Available products:
    
    D1 - DuoLife Day and Night ($29): Complete daily nutrition set with day/night formulas for overall health
    D2 - DuoLife Vita C ($39): 100% natural vitamin C liquid for immune support and collagen synthesis  
    D3 - DuoLife Collagen ($55): Premium anti-aging liquid collagen for skin, joints, and bones
    D4 - DuoLife Aloes ($25): Pure aloe vera liquid for digestive health and natural detoxification
    D5 - DuoLife Chlorofil ($25): High chlorophyll liquid for blood purification and energy boost
    
    Choose the most appropriate product based on customer's health goals and needs.
    
    Args:
        agent_id: ID of the agent showing products
        customer_name: Name of the customer
        health_goals: Customer's health goals (e.g., "immune support", "anti-aging", "detox")
        budget_preference: Budget preference ("standard" or "premium")
        specific_needs: Specific health requirements or concerns
        
    Returns:
        Detailed product recommendation with complete information including image path
    """
    # Get product recommendation based on customer needs
    needs_text = f"{health_goals or ''} {specific_needs or ''}".strip()
    
    if needs_text:
        recommended_product = get_product_recommendation(needs_text, budget_preference)
    else:
        # Default to most popular product
        recommended_product = get_product_by_id("D2")  # DuoLife Vita C
    
    if not recommended_product:
        recommended_product = get_product_by_id("D1")  # Fallback to complete set
    
    # Format features as bullet points
    features_text = "\n".join(f"  • {feature}" for feature in recommended_product["key_features"])
    
    # Get image path based on product ID (D1->1.png, D2->2.png, etc.)
    product_number = recommended_product["id"][1]  # Extract number from D1, D2, etc.
    image_path = f"../data/images/{product_number}.png"
    
    recommendation = f"""
Hello {customer_name}! Based on your health goals, I recommend:

🌿 **{recommended_product['name']}** ({recommended_product['type']})

💰 **Price:** {recommended_product['price']}

📋 **Key Benefits:**
{features_text}

📝 **Description:** {recommended_product['description']}

🎯 **Health Effects:** {recommended_product['health_effects']}

🖼️ **Product Image:** {image_path}

This {recommended_product['category'].lower()} is perfect for your {health_goals or 'wellness'} goals and would be an excellent addition to your daily health routine.

Would you like to know more about this product, or would you prefer to see other options from our DuoLife range?
    """.strip()
    
    return recommendation

# ===============================
# TOOL REGISTRY & EXECUTION ENGINE
# ===============================

# Registry of all available tools
TOOL_REGISTRY = {
    "send_email": send_email,
    "get_recent_emails": get_recent_emails,
    "check_availability": check_availability,
    "get_events": get_events,
    "book_appointment": book_appointment,
    "update_event": update_event,
    "delete_event": delete_event,
    "append_or_update_lead": append_or_update_lead,
    "get_lead_rows": get_lead_rows,
    "escalate_to_human": escalate_to_human,
    "show_product": show_product
}

# Tool metadata for agent configuration
TOOL_METADATA = {
    "send_email": {
        "name": "Send Email",
        "description": "Send emails to customers via Gmail integration",
        "category": "communication",
        "required": False
    },
    "get_recent_emails": {
        "name": "Get Recent Emails", 
        "description": "Retrieve recent email conversations with customers",
        "category": "communication",
        "required": False
    },
    "check_availability": {
        "name": "Check Availability",
        "description": "Check calendar availability for scheduling meetings",
        "category": "scheduling",
        "required": False
    },
    "get_events": {
        "name": "Get Calendar Events",
        "description": "Retrieve calendar events and meeting details",
        "category": "scheduling", 
        "required": False
    },
    "book_appointment": {
        "name": "Book Appointment",
        "description": "Schedule new appointments with customers",
        "category": "scheduling",
        "required": False
    },
    "update_event": {
        "name": "Update Event",
        "description": "Modify existing calendar events and appointments",
        "category": "scheduling",
        "required": False
    },
    "delete_event": {
        "name": "Delete Event", 
        "description": "Cancel and remove calendar events",
        "category": "scheduling",
        "required": False
    },
    "append_or_update_lead": {
        "name": "Update Lead Info",
        "description": "Capture and update customer lead information",
        "category": "lead_management",
        "required": True  # This is typically required for most agents
    },
    "get_lead_rows": {
        "name": "Get Lead Info",
        "description": "Retrieve existing customer lead information",
        "category": "lead_management", 
        "required": False
    },
    "escalate_to_human": {
        "name": "Transfer to Human",
        "description": "Escalate complex queries to human agents",
        "category": "support",
        "required": True  # Always needed as a fallback
    },
    "show_product": {
        "name": "Show DuoLife Products",
        "description": "Present DuoLife health product recommendations with 5 available products: Day&Night set ($29), Vita C immune support ($39), Collagen anti-aging ($55), Aloes digestive health ($25), Chlorofil energy boost ($25)",
        "category": "sales",
        "required": False
    }
}

def get_available_tools() -> List[Dict[str, Any]]:
    """Get list of all available tools with metadata"""
    return [
        {
            "id": tool_id,
            "name": metadata["name"],
            "description": metadata["description"],
            "category": metadata["category"],
            "required": metadata["required"]
        }
        for tool_id, metadata in TOOL_METADATA.items()
    ]

def get_tools_by_ids(tool_ids: List[str]) -> List:
    """Get tool functions by their IDs for agent configuration"""
    return [TOOL_REGISTRY[tool_id] for tool_id in tool_ids if tool_id in TOOL_REGISTRY]

def get_agent_tools(agent_id: int) -> List:
    """Get all tools available for an agent based on their enabled tools in database
    
    Args:
        agent_id: ID of the agent
        
    Returns:
        List of tool functions available for this agent
    """
    try:
        from models import get_db
        from services.database_service import DatabaseService
        
        # Get agent from database
        db = next(get_db())
        agent = DatabaseService.get_agent(db, agent_id)
        
        if not agent or not agent.enabled_tools:
            # Return basic tools if no specific tools configured
            return [
                append_or_update_lead,
                escalate_to_human,
                show_product
            ]
        
        # Parse enabled tools
        import json
        try:
            enabled_tool_ids = json.loads(agent.enabled_tools)
        except (json.JSONDecodeError, TypeError):
            enabled_tool_ids = []
        
        # Get the corresponding tool functions
        agent_tools = []
        for tool_id in enabled_tool_ids:
            if tool_id in TOOL_REGISTRY:
                agent_tools.append(TOOL_REGISTRY[tool_id])
        
        # Always include essential tools
        essential_tools = [append_or_update_lead, escalate_to_human, show_product]
        for tool in essential_tools:
            if tool not in agent_tools:
                agent_tools.append(tool)
        
        return agent_tools
        
    except Exception as e:
        logger.error(f"Error getting tools for agent {agent_id}: {str(e)}")
        # Fallback to basic tools
        return [
            append_or_update_lead,
            escalate_to_human,
            show_product
        ]

async def execute_tool(tool_name: str, agent_id: int, **kwargs) -> ToolResponse:
    """Execute a tool by name with given parameters"""
    if tool_name not in TOOL_REGISTRY:
        return ToolResponse(
            success=False,
            message="",
            error=f"Tool '{tool_name}' not found in registry"
        )
    
    try:
        tool_func = TOOL_REGISTRY[tool_name]
        result = await tool_func(agent_id=agent_id, **kwargs)
        return ToolResponse(success=True, message=str(result))
    except Exception as e:
        logger.error(f"Tool execution failed for {tool_name}: {str(e)}")
        return ToolResponse(
            success=False,
            message="",
            error=f"Tool execution failed: {str(e)}"
        )
