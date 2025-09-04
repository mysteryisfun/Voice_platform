"""
Agent management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from models import get_db
from models.database import Agent, OnboardingSession, KnowledgeChunk
from services.database_service import DatabaseService
from services.chromadb_service import ChromaDBService

router = APIRouter()
chromadb_service = ChromaDBService()


@router.get("/agents")
async def list_agents(db: Session = Depends(get_db)):
    """List all created agents with their statistics"""
    try:
        agents = DatabaseService.list_agents(db)
        
        agent_list = []
        for agent in agents:
            # Get knowledge base stats
            knowledge_stats = chromadb_service.get_collection_stats(agent.id)
            
            # Get onboarding session info
            session = db.query(OnboardingSession).filter(OnboardingSession.agent_id == agent.id).first()
            
            agent_data = {
                "id": agent.id,
                "name": agent.name or f"Agent {agent.id}",
                "company_name": agent.company_name,
                "status": agent.status,
                "personality": agent.personality,
                "tone": agent.tone,
                "language": agent.language,
                "created_at": agent.created_at.isoformat() if agent.created_at else None,
                "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
                "knowledge_chunks": knowledge_stats.get("document_count", 0),
                "questions_answered": len(session.questions_and_answers or []) if session else 0,
                "is_configured": bool(agent.name and agent.company_name and agent.system_prompt)
            }
            agent_list.append(agent_data)
        
        return {
            "agents": agent_list,
            "total": len(agent_list),
            "configured_count": len([a for a in agent_list if a["is_configured"]]),
            "message": "Agents retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agents: {str(e)}")


@router.get("/agents/{agent_id}")
async def get_agent_details(agent_id: int, db: Session = Depends(get_db)):
    """Get detailed agent information including knowledge base stats"""
    try:
        agent = DatabaseService.get_agent(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get onboarding session with Q&A history
        session = db.query(OnboardingSession).filter(OnboardingSession.agent_id == agent_id).first()
        
        # Get knowledge base statistics
        knowledge_stats = chromadb_service.get_collection_stats(agent_id)
        
        # Get knowledge chunks breakdown
        chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.agent_id == agent_id).all()
        content_types = {}
        for chunk in chunks:
            content_type = chunk.content_type
            if content_type not in content_types:
                content_types[content_type] = 0
            content_types[content_type] += 1
        
        return {
            "id": agent.id,
            "name": agent.name,
            "company_name": agent.company_name,
            "description": agent.description,
            "status": agent.status,
            "personality": agent.personality,
            "tone": agent.tone,
            "language": agent.language,
            "system_prompt": agent.system_prompt,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
            "knowledge_base": {
                "total_chunks": knowledge_stats.get("document_count", 0),
                "content_breakdown": content_types,
                "collection_name": knowledge_stats.get("collection_name")
            },
            "onboarding": {
                "questions_answered": len(session.questions_and_answers or []) if session else 0,
                "qa_history": session.questions_and_answers if session else [],
                "status": session.status if session else "not_started",
                "completed_at": session.completed_at.isoformat() if session and session.completed_at else None
            },
            "is_configured": bool(agent.name and agent.company_name and agent.system_prompt)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agent details: {str(e)}")


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    """Delete agent and all associated data"""
    try:
        agent = DatabaseService.get_agent(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Delete ChromaDB collection
        chromadb_service.delete_agent_collection(agent_id)
        
        # Delete knowledge chunks
        db.query(KnowledgeChunk).filter(KnowledgeChunk.agent_id == agent_id).delete()
        
        # Delete onboarding session
        db.query(OnboardingSession).filter(OnboardingSession.agent_id == agent_id).delete()
        
        # Delete agent
        db.query(Agent).filter(Agent.id == agent_id).delete()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Agent {agent_id} and all associated data deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")


@router.put("/agents/{agent_id}/status")
async def update_agent_status(agent_id: int, status_data: Dict[str, str], db: Session = Depends(get_db)):
    """Update agent status (activate/deactivate)"""
    try:
        agent = DatabaseService.get_agent(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        new_status = status_data.get("status")
        if new_status not in ["active", "inactive", "deployed", "created"]:
            raise HTTPException(status_code=400, detail="Invalid status. Must be: active, inactive, deployed, or created")
        
        agent.status = new_status
        agent.updated_at = datetime.now()
        
        db.commit()
        db.refresh(agent)
        
        return {
            "success": True,
            "agent_id": agent_id,
            "new_status": new_status,
            "message": f"Agent status updated to {new_status}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update agent status: {str(e)}")
