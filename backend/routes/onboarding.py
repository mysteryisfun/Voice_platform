"""
Onboarding flow endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from models import get_db
from models.database import Agent, OnboardingSession
from schemas import (
    OnboardingStartRequest, OnboardingStartResponse,
    OnboardingAnswerRequest, OnboardingAnswerResponse,
    OnboardingStatusResponse, OnboardingCompleteRequest, OnboardingCompleteResponse,
    OnboardingConfigRequest, VoiceOption, AvailableToolOption
)
from schemas.simple_complete import SimpleCompleteRequest
from services.openai_service import OpenAIService
from services.database_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter()
openai_service = OpenAIService()


@router.post("/onboarding/start", response_model=OnboardingStartResponse)
async def start_onboarding(request: OnboardingStartRequest, db: Session = Depends(get_db)):
    """Initialize new onboarding session"""
    try:
        # Create agent and session
        agent, session = DatabaseService.create_agent_and_session(db, request.initial_context)
        
        # Generate first question
        first_question = openai_service.generate_first_question(request.initial_context)
        
        # Store the first question in the session
        DatabaseService.set_current_question(db, session.id, first_question)
        
        return OnboardingStartResponse(
            session_id=str(session.id),
            agent_id=agent.id,
            first_question=first_question,
            status="started"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start onboarding: {str(e)}")


@router.post("/onboarding/answer", response_model=OnboardingAnswerResponse)
async def submit_answer(request: OnboardingAnswerRequest, db: Session = Depends(get_db)):
    """Submit user response and get next AI question"""
    try:
        session_id = int(request.session_id)
        
        # Get current session
        session = DatabaseService.get_onboarding_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        print(f"DEBUG: Before update - Q&A count: {len(session.questions_and_answers or [])}")
        print(f"DEBUG: Current Q&A history: {session.questions_and_answers}")
        
        # Get the actual question that was asked
        current_question = session.current_question
        if not current_question:
            # Fallback if no question stored (shouldn't happen in normal flow)
            current_question = f"Question {request.question_number}"
        
        # Add Q&A to session
        updated_session = DatabaseService.add_question_answer(
            db, session_id, current_question, request.answer
        )
        
        print(f"DEBUG: After update - Q&A count: {len(updated_session.questions_and_answers or [])}")
        print(f"DEBUG: Updated Q&A history: {updated_session.questions_and_answers}")
        
        # Get Q&A history for context
        qa_history = updated_session.questions_and_answers or []
        
        print(f"DEBUG: Sending to OpenAI - QA count: {len(qa_history)}")
        
        # Generate next question
        next_result = openai_service.generate_next_question(qa_history, len(qa_history))
        
        print(f"DEBUG: OpenAI response: {next_result}")
        
        # Store the next question if not complete
        if not next_result.get("is_complete", False) and next_result.get("question"):
            DatabaseService.set_current_question(db, session_id, next_result["question"])
        
        return OnboardingAnswerResponse(
            session_id=str(session_id),
            next_question=next_result.get("question"),
            is_complete=next_result.get("is_complete", False),
            progress=f"{updated_session.total_questions_asked}/{updated_session.total_questions_asked + (0 if next_result.get('is_complete') else 1)}",
            total_questions=updated_session.total_questions_asked
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process answer: {str(e)}")


@router.get("/onboarding/status/{session_id}", response_model=OnboardingStatusResponse)
async def get_onboarding_status(session_id: str, db: Session = Depends(get_db)):
    """Check onboarding processing progress"""
    try:
        session = DatabaseService.get_onboarding_session(db, int(session_id))
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Calculate progress percentage
        total_steps = 3  # Q&A, web scraping, document processing, vector embedding
        completed_steps = 0
        
        if session.status in ["completed"]:
            completed_steps = 3
        elif session.status == "processing_data":
            completed_steps = 1
        elif session.status == "in_progress":
            completed_steps = 0.5
        
        progress_percentage = int((completed_steps / total_steps) * 100)
        
        return OnboardingStatusResponse(
            session_id=str(session.id),
            agent_id=session.agent_id,
            status=session.status,
            current_question_number=session.current_question_number,
            total_questions_asked=session.total_questions_asked,
            web_scraping_status=session.web_scraping_status,
            document_processing_status=session.document_processing_status,
            vector_embedding_status=session.vector_embedding_status,
            progress_percentage=progress_percentage
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/onboarding/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding(request: OnboardingCompleteRequest, db: Session = Depends(get_db)):
    """Finalize configuration and start agent creation with meta agent"""
    try:
        session_id = int(request.session_id)
        config = request.configuration
        
        # Get session
        session = DatabaseService.get_onboarding_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Extract info from Q&A history and configuration
        qa_history = session.questions_and_answers or []
        
        # Use configuration data
        agent_name = config.identity_config.agent_name
        company_name = None
        
        # Extract company name from Q&A if available
        for qa in qa_history:
            if "company" in qa.get("question", "").lower():
                company_name = qa.get("answer", "").split()[0]  # Simple extraction
                break
        
        # Prepare agent data for meta agent
        agent_data = {
            'agent_name': agent_name,
            'company_name': company_name or "Your Company",
            'business_type': config.identity_config.business_type if hasattr(config.identity_config, 'business_type') else "General Business",
            'agent_role': config.identity_config.agent_role if hasattr(config.identity_config, 'agent_role') else "Assistant",
            'voice_id': config.voice_config.voice_id if hasattr(config.voice_config, 'voice_id') else 'alloy',
            'speaking_speed': getattr(config.voice_config, 'speaking_speed', 'normal'),
            'enabled_tools': config.tools_config.enabled_tools if hasattr(config.tools_config, 'enabled_tools') else [],
            'qa_history': qa_history,
            'session_id': session_id
        }
        
        # Create agent with initializing status first
        agent = Agent(
            name=agent_name,
            company_name=company_name or "Your Company",
            business_type=agent_data['business_type'],
            status='initializing',
            is_configured=False,
            created_at=datetime.utcnow()
        )
        
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
        # Store agent_id in agent_data for meta agent
        agent_data['agent_id'] = agent.id
        
        # Import and use meta agent asynchronously
        import asyncio
        from voice_agents.agent_builder import agent_builder
        
        async def build_agent_async():
            try:
                # Build agent configuration using meta agent
                agent_components = await agent_builder.build_agent_configuration(agent_data)
                
                # Update agent with generated configuration
                agent_record = db.query(Agent).filter(Agent.id == agent.id).first()
                if agent_record:
                    agent_record.greeting_message = agent_components.greeting_script
                    agent_record.special_instructions = f"Role: {agent_components.agent_role_description}. Personality: {agent_components.personality_traits}"
                    agent_record.escalation_triggers = agent_components.escalation_rules
                    agent_record.status = 'created'
                    agent_record.is_configured = True
                    agent_record.system_prompt = agent_components.model_dump_json()  # Store complete configuration
                    
                    db.commit()
                    print(f"Agent {agent.id} successfully configured with meta agent")
                    
            except Exception as e:
                print(f"Error building agent {agent.id}: {str(e)}")
                # Update agent status to error
                agent_record = db.query(Agent).filter(Agent.id == agent.id).first()
                if agent_record:
                    agent_record.status = 'error'
                    agent_record.special_instructions = f"Configuration failed: {str(e)}"
                    db.commit()
        
        # Run the async building process in background
        asyncio.create_task(build_agent_async())
        
        return OnboardingCompleteResponse(
            agent_id=agent.id,
            agent_name=agent.name,
            status='initializing',  # Status while meta agent processes
            system_prompt="",  # Will be filled by meta agent
            knowledge_chunks_count=0,
            message="Agent initialization started with meta agent"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete onboarding: {str(e)}")


@router.post("/complete")
async def complete_simple_onboarding(request: SimpleCompleteRequest, db: Session = Depends(get_db)):
    """Complete onboarding with simple frontend request structure"""
    try:
        # Get session
        session = DatabaseService.get_onboarding_session(db, int(request.session_id))
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Prepare agent data for meta agent
        agent_data = {
            'agent_name': request.agent_name,
            'company_name': request.business_type,  # Using business_type as company name
            'business_type': request.business_type,
            'agent_role': request.agent_role,
            'voice_id': request.voice_id,
            'speaking_speed': 'normal',
            'enabled_tools': request.enabled_tools,
            'qa_history': session.questions_and_answers or [],
            'session_id': request.session_id
        }
        
        # Create agent with initializing status first
        agent = Agent(
            name=request.agent_name,
            company_name=request.business_type,
            industry=request.business_type,
            agent_role=request.agent_role,
            voice_id=request.voice_id,
            enabled_tools=request.enabled_tools,
            status='initializing'  # Start with initializing, will progress through configuring -> deploying -> created
        )
        
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
        # Store agent_id in agent_data for meta agent
        agent_data['agent_id'] = agent.id
        
        # Import and use meta agent asynchronously
        import asyncio
        from voice_agents.agent_builder import VoiceAgentBuilder
        
        async def build_agent_async():
            try:
                # Step 1: Update status to configuring
                agent_record = db.query(Agent).filter(Agent.id == agent.id).first()
                if agent_record:
                    agent_record.status = 'configuring'
                    db.commit()
                
                # Step 2: Initialize the agent builder and build configuration
                builder = VoiceAgentBuilder()
                agent_components = await builder.build_agent_configuration(agent_data)
                
                # Step 3: Update agent with generated configuration
                agent_record = db.query(Agent).filter(Agent.id == agent.id).first()
                if agent_record:
                    agent_record.greeting_message = agent_components.greeting_script
                    agent_record.special_instructions = f"Role: {agent_components.agent_role_description}. Personality: {agent_components.personality_traits}"
                    agent_record.escalation_triggers = agent_components.escalation_rules
                    agent_record.system_prompt = agent_components.model_dump_json()  # Store complete configuration
                    agent_record.is_configured = True
                    agent_record.status = 'deploying'  # Move to deploying status
                    db.commit()
                    logger.info(f"Agent {agent.id} configuration completed, moving to deployment")
                
                # Step 4: TODO - LiveKit integration and deployment
                # For now, simulate deployment delay
                import time
                await asyncio.sleep(2)  # Simulate deployment time
                
                # Step 5: Mark as fully created only after everything is done
                agent_record = db.query(Agent).filter(Agent.id == agent.id).first()
                if agent_record:
                    agent_record.status = 'created'  # Only set to created when everything is complete
                    db.commit()
                    logger.info(f"Agent {agent.id} fully created and deployed")
                    
            except Exception as e:
                logger.error(f"Error building agent {agent.id}: {str(e)}")
                # Update agent status to error
                agent_record = db.query(Agent).filter(Agent.id == agent.id).first()
                if agent_record:
                    agent_record.status = 'error'
                    agent_record.special_instructions = f"Configuration failed: {str(e)}"
                    db.commit()
        
        # Run the async building process in background
        asyncio.create_task(build_agent_async())
        
        return {
            "success": True,
            "message": "Agent creation started - your agent is being built",
            "agent_id": agent.id,
            "agent_name": agent.name,
            "status": "initializing",
            "estimated_time": "2-3 minutes"
        }
        
    except Exception as e:
        logger.error(f"Error completing simple onboarding: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to complete onboarding: {str(e)}")


@router.get("/onboarding/voice-options")
async def get_voice_options():
    """Get available voice options for agent configuration"""
    voices = [
        VoiceOption(
            id="alloy",
            name="Alloy",
            description="Neutral, balanced voice suitable for professional interactions"
        ),
        VoiceOption(
            id="echo",
            name="Echo", 
            description="Clear, articulate voice with slight warmth"
        ),
        VoiceOption(
            id="fable",
            name="Fable",
            description="Warm, engaging voice perfect for storytelling and customer service"
        ),
        VoiceOption(
            id="onyx",
            name="Onyx",
            description="Deep, authoritative voice ideal for formal business contexts"
        ),
        VoiceOption(
            id="nova",
            name="Nova",
            description="Bright, energetic voice great for sales and marketing"
        ),
        VoiceOption(
            id="shimmer",
            name="Shimmer",
            description="Soft, gentle voice perfect for support and assistance"
        ),
        VoiceOption(
            id="coral",
            name="Coral",
            description="Friendly, approachable voice suitable for all interactions"
        )
    ]
    return {"voices": voices}


@router.get("/onboarding/tool-options")
async def get_tool_options():
    """Get available tool options for agent configuration"""
    tools = [
        AvailableToolOption(
            id="knowledge_base",
            name="Knowledge Base Q&A",
            description="Answer questions using your business information and documents",
            category="information",
            required=True
        ),
        AvailableToolOption(
            id="lead_capture",
            name="Lead Capture",
            description="Collect visitor contact information and requirements",
            category="sales"
        ),
        AvailableToolOption(
            id="appointment_booking",
            name="Appointment Booking",
            description="Schedule meetings and consultations with your team",
            category="scheduling"
        ),
        AvailableToolOption(
            id="contact_info",
            name="Contact Information",
            description="Provide business hours, location, and contact details",
            category="information"
        ),
        AvailableToolOption(
            id="gmail_integration",
            name="Gmail Integration",
            description="Send emails and manage email communication through Gmail",
            category="communication"
        ),
        AvailableToolOption(
            id="google_calendar",
            name="Google Calendar",
            description="Check availability and schedule appointments in Google Calendar",
            category="scheduling"
        ),
        AvailableToolOption(
            id="human_transfer",
            name="Transfer to Human",
            description="Escalate conversations to human representatives when needed",
            category="escalation",
            required=True
        )
    ]
    return {"tools": tools}
