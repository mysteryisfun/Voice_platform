"""
Onboarding flow endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db
from schemas import (
    OnboardingStartRequest, OnboardingStartResponse,
    OnboardingAnswerRequest, OnboardingAnswerResponse,
    OnboardingStatusResponse, OnboardingCompleteRequest, OnboardingCompleteResponse
)
from services.openai_service import OpenAIService
from services.database_service import DatabaseService

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
        
        # We need to reconstruct the question that was asked
        # For now, we'll use a placeholder - in production, we'd store the asked question
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
    """Finalize configuration and start agent creation"""
    try:
        session_id = int(request.session_id)
        
        # Get session
        session = DatabaseService.get_onboarding_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Extract info from Q&A history
        qa_history = session.questions_and_answers or []
        
        # Simple extraction - in real implementation, you'd use more sophisticated parsing
        company_name = "Sample Company"  # Extract from Q&A
        agent_name = f"{company_name} Voice Assistant"
        
        # Generate system prompt
        system_prompt = openai_service.generate_system_prompt(qa_history, company_name)
        
        # Complete onboarding
        agent = DatabaseService.complete_onboarding(
            db, session_id, system_prompt, agent_name, company_name
        )
        
        return OnboardingCompleteResponse(
            agent_id=agent.id,
            agent_name=agent.name,
            status=agent.status,
            system_prompt=system_prompt,
            knowledge_chunks_count=0,  # Will be updated when we implement knowledge processing
            message="Onboarding completed successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete onboarding: {str(e)}")
