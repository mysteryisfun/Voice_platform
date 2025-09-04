"""
Voice Agent Control API Routes
Handles voice agent deployment and room management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import asyncio
import subprocess
import os
import signal
import jwt
import time
from dotenv import load_dotenv
load_dotenv()
from models import get_db
from models.database import Agent, VoiceSession
from services.database_service import DatabaseService

router = APIRouter()

# Track running agent workers
active_workers: Dict[int, Dict[str, Any]] = {}

# LiveKit configuration from environment variables
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_WS_URL = os.getenv("LIVEKIT_URL")  # Using LIVEKIT_URL from your .env


def generate_access_token(room_name: str, participant_name: str, permissions: Dict[str, bool] = None) -> str:
    """Generate LiveKit access token for room connection"""
    if permissions is None:
        permissions = {
            "canPublish": True,
            "canSubscribe": True,
            "canPublishData": True,
            "canUpdateMetadata": True
        }
    
    # Token payload
    now = int(time.time())
    payload = {
        "iss": LIVEKIT_API_KEY,
        "sub": participant_name,
        "aud": "livekit",
        "exp": now + 3600,  # 1 hour expiration
        "nbf": now - 10,    # Allow 10 seconds clock skew
        "room": room_name,
        "permissions": permissions
    }
    
    # Generate JWT token
    token = jwt.encode(payload, LIVEKIT_API_SECRET, algorithm="HS256")
    return token


class VoiceSessionManager:
    """Manages voice sessions and LiveKit rooms"""
    
    @staticmethod
    def generate_room_name(agent_id: int) -> str:
        """Generate unique room name for agent session"""
        session_id = str(uuid.uuid4())[:8]
        return f"agent-{agent_id}-{session_id}"
    
    @staticmethod
    def create_voice_session(db: Session, agent_id: int, room_name: str) -> VoiceSession:
        """Create a new voice session record"""
        session = VoiceSession(
            agent_id=agent_id,
            room_name=room_name,
            status='created',
            created_at=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session


@router.post("/voice/{agent_id}/deploy")
async def deploy_voice_agent(agent_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Deploy a voice agent to LiveKit"""
    try:
        # Get agent
        agent = DatabaseService.get_agent(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent.status != 'created':
            raise HTTPException(status_code=400, detail=f"Agent must be in 'created' status, currently: {agent.status}")
        
        # Check if agent is already deployed
        if agent_id in active_workers:
            return {
                "success": True,
                "message": "Agent is already deployed",
                "agent_id": agent_id,
                "status": "deployed",
                "worker_info": active_workers[agent_id]
            }
        
        # Start the voice agent worker
        def start_worker():
            try:
                # Get the project root directory
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                voice_agent_path = os.path.join(project_root, "voice_agents", "voice_agent.py")
                
                # Set environment variables for the worker
                env = os.environ.copy()
                env['AGENT_ID'] = str(agent_id)
                
                # Start the worker process
                process = subprocess.Popen(
                    ["python", voice_agent_path],
                    cwd=project_root,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Track the worker
                active_workers[agent_id] = {
                    "process": process,
                    "started_at": datetime.utcnow().isoformat(),
                    "status": "running"
                }
                
                # Update agent status
                agent.status = 'deployed'
                agent.updated_at = datetime.utcnow()
                db.commit()
                
                print(f"Voice agent {agent_id} deployed successfully")
                
            except Exception as e:
                print(f"Error starting worker for agent {agent_id}: {str(e)}")
                # Update agent status to error
                agent.status = 'error'
                agent.special_instructions = f"Deployment failed: {str(e)}"
                db.commit()
        
        # Start worker in background
        background_tasks.add_task(start_worker)
        
        return {
            "success": True,
            "message": "Voice agent deployment started",
            "agent_id": agent_id,
            "status": "deploying"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deploy voice agent: {str(e)}")


@router.post("/voice/{agent_id}/stop")
async def stop_voice_agent(agent_id: int, db: Session = Depends(get_db)):
    """Stop a deployed voice agent"""
    try:
        # Get agent
        agent = DatabaseService.get_agent(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check if agent is deployed
        if agent_id not in active_workers:
            return {
                "success": True,
                "message": "Agent is not currently deployed",
                "agent_id": agent_id,
                "status": "stopped"
            }
        
        # Stop the worker process
        worker_info = active_workers[agent_id]
        process = worker_info.get("process")
        
        if process and process.poll() is None:  # Process is still running
            process.terminate()
            try:
                process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
            except subprocess.TimeoutExpired:
                process.kill()  # Force kill if needed
        
        # Remove from active workers
        del active_workers[agent_id]
        
        # Update agent status
        agent.status = 'created'
        agent.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": "Voice agent stopped successfully",
            "agent_id": agent_id,
            "status": "stopped"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop voice agent: {str(e)}")


@router.get("/voice/{agent_id}/status")
async def get_voice_agent_status(agent_id: int, db: Session = Depends(get_db)):
    """Get status of a voice agent"""
    try:
        # Get agent
        agent = DatabaseService.get_agent(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check worker status
        is_deployed = agent_id in active_workers
        worker_status = "stopped"
        worker_info = None
        
        if is_deployed:
            worker_info = active_workers[agent_id]
            process = worker_info.get("process")
            
            if process and process.poll() is None:
                worker_status = "running"
            else:
                worker_status = "stopped"
                # Clean up dead worker
                del active_workers[agent_id]
        
        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "agent_status": agent.status,
            "worker_status": worker_status,
            "is_deployed": is_deployed,
            "worker_info": worker_info,
            "last_updated": agent.updated_at.isoformat() if agent.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get voice agent status: {str(e)}")


@router.post("/voice/{agent_id}/session")
async def create_voice_session(agent_id: int, db: Session = Depends(get_db)):
    """Create a new voice session for an agent"""
    try:
        # Get agent
        agent = DatabaseService.get_agent(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent.status not in ['created', 'deployed']:
            raise HTTPException(status_code=400, detail=f"Agent is not ready for sessions (status: {agent.status})")
        
        # Generate room name
        room_name = VoiceSessionManager.generate_room_name(agent_id)
        
        # Create session record
        session = VoiceSessionManager.create_voice_session(db, agent_id, room_name)
        
        # Generate LiveKit connection token (you'll need to implement this based on your LiveKit setup)
        # For now, we'll return the room name for the frontend to connect
        
        return {
            "success": True,
            "session_id": session.id,
            "room_name": room_name,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "voice_id": agent.voice_id or 'alloy',
            "status": "ready",
            "message": "Voice session created successfully",
            # Add LiveKit connection info
            "livekit_token": generate_access_token(room_name, f"user-{session.id}"),
            "livekit_ws_url": LIVEKIT_WS_URL
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create voice session: {str(e)}")


@router.get("/voice/{agent_id}/sessions")
async def list_voice_sessions(agent_id: int, db: Session = Depends(get_db)):
    """List all voice sessions for an agent"""
    try:
        # Get agent
        agent = DatabaseService.get_agent(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get sessions from database
        sessions = db.query(VoiceSession).filter(VoiceSession.agent_id == agent_id).order_by(VoiceSession.created_at.desc()).limit(10).all()
        
        session_list = []
        for session in sessions:
            session_data = {
                "id": session.id,
                "room_name": session.room_name,
                "status": session.status,
                "created_at": session.created_at.isoformat(),
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "duration_seconds": session.duration_seconds
            }
            session_list.append(session_data)
        
        return {
            "agent_id": agent_id,
            "sessions": session_list,
            "total_sessions": len(session_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list voice sessions: {str(e)}")


@router.get("/voice/workers")
async def list_active_workers():
    """List all active voice agent workers"""
    try:
        worker_status = {}
        
        for agent_id, worker_info in active_workers.items():
            process = worker_info.get("process")
            status = "running" if process and process.poll() is None else "stopped"
            
            worker_status[agent_id] = {
                "agent_id": agent_id,
                "status": status,
                "started_at": worker_info.get("started_at"),
                "process_id": process.pid if process else None
            }
        
        return {
            "active_workers": worker_status,
            "total_workers": len(active_workers)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workers: {str(e)}")
