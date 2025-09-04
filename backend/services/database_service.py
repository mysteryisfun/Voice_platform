"""
Database service for agent and onboarding operations
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from datetime import datetime
import json
import uuid

from models.database import Agent, OnboardingSession, AgentStatus, OnboardingStatus
from schemas import QuestionAndAnswer


class DatabaseService:
    @staticmethod
    def create_agent_and_session(db: Session, initial_context: str = None) -> tuple[Agent, OnboardingSession]:
        """Create a new agent and onboarding session"""
        
        # Create agent with onboarding status
        agent = Agent(
            name=None,  # Will be filled during onboarding
            description="Agent created via onboarding process",
            company_name=None,  # Will be filled during onboarding
            status=AgentStatus.CREATED,
            personality="professional",  # Default, can be updated
            tone="helpful",  # Default, can be updated
            language="en"
        )   
        
        db.add(agent)
        db.flush()  # Get the agent ID
        
        # Create onboarding session linked to agent
        session = OnboardingSession(
            agent_id=agent.id,
            status=OnboardingStatus.STARTED,
            current_question_number=1,
            total_questions_asked=0,
            questions_and_answers=[],
            current_question=None,  # Will be set when first question is generated
            web_scraping_status="pending",
            document_processing_status="pending", 
            vector_embedding_status="pending"
        )
        
        db.add(session)
        db.commit()
        db.refresh(agent)
        db.refresh(session)
        
        return agent, session
    
    @staticmethod
    def get_onboarding_session(db: Session, session_id: int) -> Optional[OnboardingSession]:
        """Get onboarding session by ID"""
        return db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
    
    @staticmethod
    def set_current_question(db: Session, session_id: int, question: str) -> OnboardingSession:
        """Set the current question for the session"""
        session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.current_question = question
        session.updated_at = datetime.now()
        
        db.commit()
        db.refresh(session)
        
        return session
    
    @staticmethod
    def add_question_answer(db: Session, session_id: int, question: str, answer: str) -> OnboardingSession:
        """Add Q&A to onboarding session"""
        session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get current Q&A list - handle if it's None or not a list
        try:
            qa_list = session.questions_and_answers if session.questions_and_answers else []
            if not isinstance(qa_list, list):
                qa_list = []
        except:
            qa_list = []
        
        print(f"DEBUG SERVICE: Current QA list length: {len(qa_list)}")
        
        # Add new Q&A
        qa_item = {
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat(),
            "question_number": len(qa_list) + 1
        }
        
        qa_list.append(qa_item)
        
        print(f"DEBUG SERVICE: New QA list length: {len(qa_list)}")
        print(f"DEBUG SERVICE: Adding item: {qa_item}")
        
        # Force update the JSON field
        session.questions_and_answers = qa_list
        session.total_questions_asked = len(qa_list)
        session.current_question_number = len(qa_list) + 1
        session.status = OnboardingStatus.IN_PROGRESS
        session.updated_at = datetime.now()
        
        # Mark the field as dirty to force update
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(session, "questions_and_answers")
        
        db.commit()
        db.refresh(session)
        
        print(f"DEBUG SERVICE: After commit QA list length: {len(session.questions_and_answers or [])}")
        
        return session
    
    @staticmethod
    def complete_enhanced_onboarding(db: Session, session_id: int, system_prompt: str, config) -> Agent:
        """Complete onboarding with enhanced configuration"""
        session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get associated agent
        agent = db.query(Agent).filter(Agent.id == session.agent_id).first()
        
        if not agent:
            raise ValueError(f"Agent {session.agent_id} not found")
        
        # Update agent with enhanced configuration
        agent.name = config.identity_config.agent_name
        agent.agent_role = config.identity_config.agent_role
        agent.greeting_message = config.identity_config.greeting_message
        
        # Voice configuration
        agent.voice_id = config.voice_config.voice_id
        agent.personality = config.voice_config.personality
        agent.tone = config.voice_config.tone
        agent.speaking_speed = config.voice_config.speaking_speed
        agent.response_style = config.voice_config.response_style
        
        # Tools configuration
        agent.enabled_tools = config.tools_config.enabled_tools
        agent.escalation_triggers = config.tools_config.escalation_triggers
        agent.special_instructions = config.tools_config.special_instructions
        
        # Extract company name from Q&A history if available
        qa_history = session.questions_and_answers or []
        for qa in qa_history:
            if "company" in qa.get("question", "").lower():
                agent.company_name = qa.get("answer", "").strip()
                break
        
        agent.system_prompt = system_prompt
        agent.status = AgentStatus.DEPLOYED  # Ready for deployment
        agent.updated_at = datetime.now()
        
        # Update session status
        session.status = OnboardingStatus.COMPLETED
        session.completed_at = datetime.now()
        session.updated_at = datetime.now()
        
        db.commit()
        db.refresh(agent)
        db.refresh(session)
        
        return agent
    
    @staticmethod
    def complete_onboarding(db: Session, session_id: int, system_prompt: str, agent_name: str, company_name: str) -> Agent:
        """Complete onboarding and update agent"""
        session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get associated agent
        agent = db.query(Agent).filter(Agent.id == session.agent_id).first()
        
        if not agent:
            raise ValueError(f"Agent {session.agent_id} not found")
        
        # Update agent with final information
        agent.name = agent_name
        agent.company_name = company_name
        agent.system_prompt = system_prompt
        agent.status = AgentStatus.DEPLOYED  # Ready for deployment
        agent.updated_at = datetime.now()
        
        # Update session status
        session.status = OnboardingStatus.COMPLETED
        session.completed_at = datetime.now()
        session.updated_at = datetime.now()
        
        db.commit()
        db.refresh(agent)
        db.refresh(session)
        
        return agent
    
    @staticmethod
    def get_agent(db: Session, agent_id: int) -> Optional[Agent]:
        """Get agent by ID"""
        return db.query(Agent).filter(Agent.id == agent_id).first()
    
    @staticmethod
    def list_agents(db: Session) -> List[Agent]:
        """List all agents"""
        return db.query(Agent).order_by(Agent.created_at.desc()).all()
    
    @staticmethod
    def update_processing_status(db: Session, session_id: int, 
                                web_status: str = None, 
                                doc_status: str = None, 
                                vector_status: str = None) -> OnboardingSession:
        """Update processing status for async operations"""
        session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if web_status:
            session.web_scraping_status = web_status
        if doc_status:
            session.document_processing_status = doc_status
        if vector_status:
            session.vector_embedding_status = vector_status
            
        session.updated_at = datetime.now()
        
        db.commit()
        db.refresh(session)
        
        return session
