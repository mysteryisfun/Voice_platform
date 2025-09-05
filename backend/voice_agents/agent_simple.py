from dotenv import load_dotenv
import json
import os
import sys
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(backend_dir)
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    noise_cancellation,
)
from tools_livekit import send_email, get_recent_emails, check_availability, get_events, book_appointment, update_event, delete_event, append_or_update_lead, get_lead_rows, escalate_to_human, show_product, get_agent_tools
from tools_livekit import get_agent_tools
from models import get_db_session
from models.database import Agent as AgentModel
load_dotenv(".env")


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

def load_agent_config(agent_id):
    """Load agent configuration from database"""
    try:
        db = get_db_session()
        agent_record = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
        db.close()
        
        if agent_record and agent_record.system_prompt:
            # Parse JSON system_prompt if it exists
            try:
                config = json.loads(agent_record.system_prompt)
                return config.get('instructions', 'You are a helpful AI assistant.')
            except json.JSONDecodeError:
                # If not JSON, use as plain text
                return agent_record.system_prompt
        
        return "You are a helpful AI assistant."
    except Exception as e:
        print(f"Error loading agent config: {e}")
        return "You are a helpful AI assistant."
    
def load_agent_tools(agent_id):
    """Load agent tools from tools_livekit.py"""
    try:
        tools = get_agent_tools(agent_id)
        print(f"🔧 Loaded {len(tools)} tools for agent {agent_id}")
        return tools
    except Exception as e:
        print(f"Error loading agent tools: {e}")
        return []
agent_id = 2
agent = get_agent_from_database(agent_id)
config = json.loads(agent.system_prompt)
prompt = f"""You are {agent.name}, {config.get('agent_role_description', 'a helpful assistant')}.

{config.get('greeting_script', agent.greeting_message or f'Hello! I am {agent.name}.')}

You work for {config.get('company_name', agent.company_name or 'our company')}.
{config.get('company_description', '')}

Your personality: {config.get('personality_traits', 'Professional and helpful')}
Business hours: {config.get('business_hours', '24/7')}

Respond naturally and stay in character as {agent.name}."""

all_tool_functions = [
    send_email, get_recent_emails, check_availability, get_events, 
    book_appointment, update_event, delete_event, append_or_update_lead, 
    get_lead_rows, escalate_to_human, show_product
]
#from tools import get_wheather
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=prompt, tools=all_tool_functions
                        )   
    

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice="coral"
        )
    )
    assistant = Assistant()
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` instead for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    await session.generate_reply(
        instructions="Greet the user and offer your assistance in English."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))