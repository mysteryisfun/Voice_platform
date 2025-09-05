"""
Core LiveKit voice agent implementation using OpenAI Realtime API.

This module contains the main LiveKit agent entrypoint that integrates
with our website's agent management system, tools, and database.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import openai, noise_cancellation

load_dotenv()

logger = logging.getLogger(__name__)


def get_agent_from_database(agent_id: int):
    """Get agent configuration from database"""
    try:
        from models.database import get_db_session, Agent as AgentModel
        
        # Create database session
        db = next(get_db_session())
        
        # Get agent from database
        agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
        if not agent:
            logger.warning(f"Agent {agent_id} not found in database")
            return None
            
        logger.info(f"Loaded agent {agent_id}: {agent.name}")
        return agent
        
    except Exception as e:
        logger.warning(f"Could not load agent from database: {e}")
        return None


def get_agent_instructions(agent_id: int) -> str:
    """Get agent instructions/prompt"""
    try:
        agent = get_agent_from_database(agent_id)
        if agent and agent.system_prompt:
            return agent.system_prompt
            
        # Fallback instructions
        return f"You are a helpful AI voice assistant (Agent {agent_id}). You can help users with various tasks using the available tools."
        
    except Exception as e:
        logger.error(f"Error getting agent instructions: {e}")
        return f"You are a helpful AI voice assistant (Agent {agent_id})."


def get_agent_tools(agent_id: int):
    """Get tools for the agent"""
    try:
        # Use the new tools_livekit.py if it exists, otherwise fallback to tools.py
        try:
            from voice_agents.tools_livekit import get_agent_tools as get_tools
            logger.info("Using tools_livekit.py for agent tools")
        except ImportError:
            from voice_agents.tools import get_agent_tools as get_tools
            logger.info("Using tools.py for agent tools")
        
        return get_tools(agent_id)
    except Exception as e:
        logger.warning(f"Could not load agent tools: {e}")
        # Return basic tools as fallback
        try:
            from voice_agents.tools_livekit import escalate_to_human, show_product, append_or_update_lead
            return [escalate_to_human, show_product, append_or_update_lead]
        except ImportError:
            try:
                from voice_agents.tools import escalate_to_human, show_product, append_or_update_lead
                return [escalate_to_human, show_product, append_or_update_lead]
            except Exception as e2:
                logger.error(f"Could not load fallback tools: {e2}")
                return []


def get_voice_for_agent(agent_id: int) -> str:
    """Get voice setting for agent"""
    try:
        agent = get_agent_from_database(agent_id)
        if agent and agent.voice_id:
            return agent.voice_id
        return "coral"  # Default voice
    except Exception as e:
        logger.error(f"Error getting voice for agent: {e}")
        return "coral"


class VoiceAgent(Agent):
    """Custom Voice Agent that inherits from LiveKit Agent"""
    
    def __init__(self, agent_id: int) -> None:
        self.agent_id = agent_id
        instructions = get_agent_instructions(agent_id)
        tools = get_agent_tools(agent_id)
        
        super().__init__(
            instructions=instructions,
            tools=tools
        )
        
        logger.info(f"VoiceAgent {agent_id} initialized with {len(tools)} tools")


async def entrypoint(ctx: agents.JobContext):
    """Main entrypoint for the LiveKit voice agent"""
    
    # Get agent ID from environment variable
    agent_id = int(os.getenv("AGENT_ID", "1"))
    room_name = ctx.room.name if ctx.room else "unknown"
    
    logger.info(f"Starting LiveKit agent {agent_id} in room {room_name}")
    
    try:
        # Get agent configuration
        voice = get_voice_for_agent(agent_id)
        
        # Create agent session with OpenAI Realtime API
        session = AgentSession(
            llm=openai.realtime.RealtimeModel(
                voice=voice,
                instructions="You are ready to assist users."
            )
        )
        
        # Create our custom voice agent
        assistant = VoiceAgent(agent_id)
        
        # Start the session
        await session.start(
            room=ctx.room,
            agent=assistant,
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )
        
        # Generate initial greeting
        agent_data = get_agent_from_database(agent_id)
        greeting = "Hello! I'm here to help you today."
        if agent_data and agent_data.greeting_message:
            greeting = agent_data.greeting_message
        elif agent_data and agent_data.name:
            greeting = f"Hello! I'm {agent_data.name}, your AI assistant. How can I help you today?"
            
        await session.generate_reply(
            instructions=f"Greet the user with this message: {greeting}"
        )
        
        logger.info(f"Agent {agent_id} connected successfully to room {room_name}")
        
    except Exception as e:
        logger.error(f"Error in agent entrypoint: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Provide basic fallback service
        try:
            session = AgentSession(
                llm=openai.realtime.RealtimeModel(
                    voice="coral",
                    instructions="I'm an AI assistant. I'm experiencing some technical difficulties but I'm here to help as best I can."
                )
            )
            
            fallback_assistant = VoiceAgent(agent_id)
            await session.start(
                room=ctx.room,
                agent=fallback_assistant,
                room_input_options=RoomInputOptions(
                    noise_cancellation=noise_cancellation.BVC(),
                ),
            )
            await session.generate_reply(
                instructions="Apologize for technical difficulties and offer basic assistance."
            )
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {str(fallback_error)}")


if __name__ == "__main__":
    # Run the agent worker
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))


def get_agent_instructions(agent_id: int):
    """Build system instructions for the agent"""
    try:
        # Try to get agent from database
        from services.database_service import DatabaseService
        from models import get_db
        
        db = next(get_db())
        agent_data = DatabaseService.get_agent(db, agent_id)
        
        if agent_data:
            name = agent_data.name or "AI Assistant"
            company = agent_data.company_name or "Our Company"
            voice_id = agent_data.voice_id or "alloy"
            
            # Parse system prompt if available
            system_prompt = ""
            if agent_data.system_prompt:
                try:
                    import json
                    prompt_data = json.loads(agent_data.system_prompt)
                    greeting = prompt_data.get('greeting_script', f"Hello! I'm {name}, how can I help you today?")
                    role_desc = prompt_data.get('agent_role_description', 'a helpful AI assistant')
                    
                    system_prompt = f"""You are {name}, {role_desc} for {company}.

{greeting}

You are professional, helpful, and knowledgeable. Use the available tools to assist customers:
- Use 'show_product' to recommend DuoLife health products
- Use 'append_or_update_lead' to capture customer information  
- Use 'escalate_to_human' when you need human assistance

Be conversational and natural in your responses. Keep conversations engaging and helpful.
Voice ID: {voice_id}"""
                except Exception as e:
                    logger.warning(f"Could not parse system prompt: {e}")
            
            if system_prompt:
                return system_prompt
                
            return f"""You are {name}, an AI voice assistant for {company}. 
            
You are professional, helpful, and knowledgeable. Use the available tools to assist customers:
- Use 'show_product' to recommend DuoLife health products
- Use 'append_or_update_lead' to capture customer information
- Use 'escalate_to_human' when you need human assistance

Be conversational and natural in your responses. Keep conversations engaging and helpful.
Voice ID: {voice_id}"""
        else:
            logger.warning(f"Agent {agent_id} not found in database")
    except Exception as e:
        logger.warning(f"Could not load agent from database: {e}")
    
    # Fallback instructions
    return f"""You are an AI voice assistant (Agent ID: {agent_id}).

You are professional, helpful, and knowledgeable. Use the available tools to assist customers:
- Use 'show_product' to recommend DuoLife health products  
- Use 'append_or_update_lead' to capture customer information
- Use 'escalate_to_human' when you need human assistance

Be conversational and natural in your responses. Keep conversations engaging and helpful."""


async def entrypoint(ctx: agents.JobContext):
    """LiveKit agent entrypoint - called when agent connects to room
    
    Args:
        ctx: Job context from LiveKit
    """
    try:
        # Extract agent ID from environment or room metadata
        agent_id = int(os.getenv("AGENT_ID", "1"))
        room_name = ctx.room.name
        
        # Parse agent ID from room name if available (format: "agent-{agent_id}-{session_id}")
        if room_name.startswith("agent-"):
            parts = room_name.split("-")
            if len(parts) >= 2:
                try:
                    agent_id = int(parts[1])
                except ValueError:
                    logger.warning(f"Could not parse agent ID from room name: {room_name}")
        
        logger.info(f"Starting LiveKit agent {agent_id} in room {room_name}")
        
        # Get agent configuration
        instructions = get_agent_instructions(agent_id)
        agent_tools = get_agent_tools(agent_id)
        
        # Create voice assistant with OpenAI Realtime API
        assistant = agents.voice.Agent(
            llm=openai.realtime.RealtimeModel(
                voice="coral",
                instructions=instructions,
                tools=agent_tools
            )
        )
        
        # Start the assistant
        assistant.start(ctx.room)
        
        logger.info(f"Agent {agent_id} connected successfully to room {room_name}")
        
    except Exception as e:
        logger.error(f"Error in agent entrypoint: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Provide basic fallback service
        try:
            fallback_assistant = agents.voice.Agent(
                llm=openai.realtime.RealtimeModel(
                    voice="coral",
                    instructions="I'm an AI assistant. I'm experiencing some technical difficulties but I'm here to help as best I can."
                )
            )
            fallback_assistant.start(ctx.room)
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {str(fallback_error)}")


if __name__ == "__main__":
    # Run the agent worker
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
