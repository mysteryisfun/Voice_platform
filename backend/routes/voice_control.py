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
    
    # Token payload using correct LiveKit structure
    now = int(time.time())
    payload = {
        "iss": LIVEKIT_API_KEY,
        "sub": participant_name,
        "video": {
            "room": room_name,
            "roomJoin": True,
            "canPublish": permissions.get("canPublish", True),
            "canSubscribe": permissions.get("canSubscribe", True),
            "canPublishData": permissions.get("canPublishData", True),
            "canUpdateMetadata": permissions.get("canUpdateMetadata", True)
        },
        "exp": now + 3600,  # 1 hour expiration
        "nbf": now - 10,    # Allow 10 seconds clock skew
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


@router.get("/voice/{agent_id}/status")
async def get_voice_agent_status(agent_id: int, db: Session = Depends(get_db)):
    """Get the current status of a voice agent"""
    try:
        # Get agent
        agent = DatabaseService.get_agent(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check if worker is tracked and still running
        worker_info = None
        if agent_id in active_workers:
            worker = active_workers[agent_id]
            process = worker["process"]
            
            # Check if process is still alive
            if process.poll() is None:
                worker_info = {
                    "pid": worker.get("pid", process.pid),
                    "started_at": worker["started_at"],
                    "status": "running"
                }
            else:
                # Process died, clean up and update status
                del active_workers[agent_id]
                if agent.status == 'deployed':
                    agent.status = 'error'
                    agent.special_instructions = "Worker process died unexpectedly"
                    agent.updated_at = datetime.utcnow()
                    db.commit()
        
        return {
            "agent_id": agent_id,
            "status": agent.status,
            "worker_info": worker_info,
            "last_updated": agent.updated_at.isoformat() if agent.updated_at else None,
            "error_message": agent.special_instructions if agent.status == 'error' else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")


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
                # Update agent status to deploying
                agent.status = 'deploying'
                agent.updated_at = datetime.utcnow()
                db.commit()
                
                # Get the project root directory
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                voice_agent_path = os.path.join(project_root, "voice_agents", "agent.py")
                
                # Set environment variables for the worker
                env = os.environ.copy()
                env['AGENT_ID'] = str(agent_id)
                
                # Start the worker process using LiveKit agent CLI pattern
                process = subprocess.Popen(
                    ["python", voice_agent_path, "dev"],  # Use dev mode for development
                    cwd=project_root,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait a moment to see if process starts successfully
                time.sleep(1)
                poll_result = process.poll()
                
                if poll_result is not None:
                    # Process died immediately
                    stdout, stderr = process.communicate()
                    error_msg = stderr.decode() if stderr else "Process died immediately"
                    raise Exception(f"Worker failed to start: {error_msg}")
                
                # Track the worker
                active_workers[agent_id] = {
                    "process": process,
                    "started_at": datetime.utcnow().isoformat(),
                    "status": "running",
                    "pid": process.pid
                }
                
                # Update agent status to connecting (waiting for LiveKit connection)
                agent.status = 'connecting'
                agent.updated_at = datetime.utcnow()
                db.commit()
                
                # Give it a few seconds to connect to LiveKit, then mark as deployed
                time.sleep(3)
                
                # Check if process is still running
                if process.poll() is None:
                    # Process is still running, assume connected
                    agent.status = 'deployed'
                    agent.updated_at = datetime.utcnow()
                    db.commit()
                    print(f"Voice agent {agent_id} deployed successfully (PID: {process.pid})")
                else:
                    # Process died
                    stdout, stderr = process.communicate()
                    error_msg = stderr.decode() if stderr else "Process died after starting"
                    raise Exception(f"Worker died during startup: {error_msg}")
                
            except Exception as e:
                print(f"Error starting worker for agent {agent_id}: {str(e)}")
                # Update agent status to error
                agent.status = 'error'
                agent.special_instructions = f"Deployment failed: {str(e)}"
                agent.updated_at = datetime.utcnow()
                db.commit()
                
                # Clean up worker tracking
                if agent_id in active_workers:
                    del active_workers[agent_id]
        
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
            try:
                print(f"Stopping voice agent {agent_id} (PID: {process.pid})")
                process.terminate()
                process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
                print(f"Voice agent {agent_id} stopped gracefully")
            except subprocess.TimeoutExpired:
                print(f"Force killing voice agent {agent_id} (PID: {process.pid})")
                process.kill()  # Force kill if needed
                process.wait()
        else:
            print(f"Voice agent {agent_id} process was already dead")
        
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
async def create_voice_session(agent_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a new voice session for an agent"""
    try:
        # Get agent
        agent = DatabaseService.get_agent(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Auto-deploy agent if not already deployed
        if agent.status == 'created':
            # Deploy the agent automatically
            def start_worker():
                try:
                    # Get the project root directory
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    voice_agent_path = os.path.join(project_root, "voice_agents", "agent.py")
                    
                    # Set environment variables for the worker
                    env = os.environ.copy()
                    env['AGENT_ID'] = str(agent_id)
                    
                    # Start the worker process using LiveKit agent CLI pattern
                    process = subprocess.Popen(
                        ["python", voice_agent_path, "dev"],  # Use dev mode for development
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
                    
                    print(f"Voice agent {agent_id} auto-deployed for session")
                    
                except Exception as e:
                    print(f"Error auto-deploying agent {agent_id}: {str(e)}")
                    agent.status = 'error'
                    agent.special_instructions = f"Auto-deployment failed: {str(e)}"
                    db.commit()
            
            # Start worker in background
            background_tasks.add_task(start_worker)
            agent.status = 'deploying'  # Set status immediately
            db.commit()
        
        elif agent.status not in ['deployed', 'deploying']:
            raise HTTPException(status_code=400, detail=f"Agent is not ready for sessions (status: {agent.status})")
        
        # Generate room name
        room_name = VoiceSessionManager.generate_room_name(agent_id)
        
        # Create session record
        session = VoiceSessionManager.create_voice_session(db, agent_id, room_name)
        
        # Generate token for playground testing
        playground_token = generate_access_token(room_name, f"user-{session.id}")
        
        # Print connection details for easy copying
        print(f"\n{'='*80}")
        print(f"🎤 VOICE SESSION CREATED - LIVEKIT PLAYGROUND DETAILS")
        print(f"{'='*80}")
        print(f"🏠 Room Name: {room_name}")
        print(f"🌐 WebSocket URL: {LIVEKIT_WS_URL}")
        print(f"🔑 Access Token: {playground_token}")
        print(f"{'='*80}")
        print(f"💡 COPY THESE DETAILS TO LIVEKIT PLAYGROUND:")
        print(f"   1. Go to: https://agents-playground.livekit.io")
        print(f"   2. Room Name: {room_name}")
        print(f"   3. WebSocket URL: {LIVEKIT_WS_URL}")
        print(f"   4. Access Token: {playground_token}")
        print(f"{'='*80}\n")
        
        return {
            "success": True,
            "session_id": session.id,
            "room_name": room_name,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "voice_id": agent.voice_id or 'alloy',
            "status": "ready" if agent.status == 'deployed' else "deploying",
            "message": "Voice session created successfully" if agent.status == 'deployed' else "Voice session created, agent is deploying...",
            # Add LiveKit connection info (keeping original field names for frontend compatibility)
            "livekit_token": generate_access_token(room_name, f"user-{session.id}"),
            "livekit_ws_url": LIVEKIT_WS_URL,  # Keep original field name
            # Debug info for playground testing
            "playground_info": {
                "room_name": room_name,
                "websocket_url": LIVEKIT_WS_URL,
                "token": generate_access_token(room_name, f"user-{session.id}"),
                "playground_url": "https://agents-playground.livekit.io",
                "instructions": f"Use room '{room_name}' with the provided token"
            }
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
