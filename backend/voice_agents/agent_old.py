"""
Simple Working Voice Agent - Based on context/agent.py that works
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import openai, noise_cancellation
from voice_agents.tools_livekit import get_agent_tools

load_dotenv()


def get_agent_from_database(agent_id: int):
    """Get agent configuration from database"""
    try:
        from models import get_db
        from models.database import Agent as AgentModel
        
        db = next(get_db())
        agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
        
        if agent:
            print(f"✅ Loaded agent {agent_id}: {agent.name}")
            db.close()
            return agent
        else:
            print(f"❌ Agent {agent_id} not found")
            db.close()
            return None
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None


class VoiceAssistant(Agent):
    def __init__(self, agent_id: int) -> None:
        # Get agent from database
        agent = get_agent_from_database(agent_id)
        
        if agent:
            # Parse system_prompt if it's JSON, otherwise use it directly
            if agent.system_prompt:
                try:
                    # Try to parse as JSON
                    config = json.loads(agent.system_prompt)
                    
                    # Build proper instructions from the JSON config
                    instructions = f"""You are {agent.name}, {config.get('agent_role_description', 'a helpful assistant')}.

{config.get('greeting_script', agent.greeting_message or f'Hello! I am {agent.name}.')}

You work for {config.get('company_name', agent.company_name or 'our company')}.
{config.get('company_description', '')}

Your personality: {config.get('personality_traits', 'Professional and helpful')}
Business hours: {config.get('business_hours', '24/7')}

Respond naturally and stay in character as {agent.name}."""
                    
                    print(f"✅ Parsed JSON config for {agent.name}")
                    
                except json.JSONDecodeError:
                    # If it's not JSON, use it as plain text instructions
                    instructions = agent.system_prompt
                    print(f"✅ Using plain text instructions for {agent.name}")
            else:
                instructions = agent.greeting_message or f"You are {agent.name}, a helpful AI voice assistant."
            
            name = agent.name
            print(f"✅ Voice agent initialized as: {name}")
        else:
            instructions = f"You are a helpful AI voice assistant (Agent {agent_id})."
            name = f"Agent {agent_id}"
            print(f"❌ Using fallback configuration for Agent {agent_id}")
        
        # Get agent tools from tools_livekit.py
        agent_tools = get_agent_tools(agent_id)
        print(f"🔧 Loaded {len(agent_tools)} tools")
        
        super().__init__(
            instructions=instructions,
            tools=agent_tools
        )
        
        self.agent_id = agent_id
        self.name = name


async def entrypoint(ctx: agents.JobContext):
    agent_id = int(os.getenv("AGENT_ID", "2"))
    print(f"🎯 Starting voice agent {agent_id} in room {ctx.room.name}")
    
    # Get agent configuration  
    agent = get_agent_from_database(agent_id)
    voice_id = agent.voice_id if agent and agent.voice_id else "alloy"
    
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice=voice_id
        )
    )
    
    assistant = VoiceAssistant(agent_id)
    
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
