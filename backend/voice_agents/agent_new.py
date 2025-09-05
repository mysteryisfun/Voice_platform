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


class VoiceAssistant(Agent):
    """Voice Assistant using the new LiveKit Agent pattern"""
    
    def __init__(self, agent_id: int) -> None:
        # Get agent configuration
        agent = get_agent_from_database(agent_id)
        
        if agent:
            instructions = agent.system_prompt or f"You are {agent.name}, a helpful AI voice assistant."
            name = agent.name
        else:
            instructions = f"You are a helpful AI voice assistant (Agent {agent_id}). You can help users with various tasks using the available tools."
            name = f"Agent {agent_id}"
        
        # Get agent tools
        agent_tools = get_agent_tools(agent_id)
        
        super().__init__(
            instructions=instructions,
            tools=agent_tools
        )
        
        self.agent_id = agent_id
        self.name = name
        logger.info(f"Voice Assistant {name} initialized with {len(agent_tools)} tools")


async def entrypoint(ctx: agents.JobContext):
    """Main entrypoint for the voice agent"""
    try:
        # Get agent ID from environment
        agent_id = int(os.getenv("AGENT_ID", "1"))
        logger.info(f"Starting LiveKit agent {agent_id} in room {ctx.room.name}")
        
        # Create agent session
        session = AgentSession(
            llm=openai.realtime.RealtimeModel(
                voice="coral"
            )
        )
        
        # Create voice assistant
        assistant = VoiceAssistant(agent_id)
        
        # Start the session
        await session.start(
            room=ctx.room,
            agent=assistant,
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )
        
        # Generate initial greeting
        await session.generate_reply(
            instructions="Greet the user and offer your assistance."
        )
        
        logger.info(f"Agent {agent_id} connected successfully to room {ctx.room.name}")
        
    except Exception as e:
        logger.error(f"Error in agent entrypoint: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Provide basic fallback service
        try:
            session = AgentSession(
                llm=openai.realtime.RealtimeModel(
                    voice="coral"
                )
            )
            fallback_assistant = Agent(
                instructions="I'm an AI assistant. I'm experiencing some technical difficulties but I'm here to help as best I can."
            )
            await session.start(
                room=ctx.room,
                agent=fallback_assistant
            )
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {str(fallback_error)}")


if __name__ == "__main__":
    # Run the agent worker
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
