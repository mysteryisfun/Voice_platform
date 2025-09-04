"""
Data processing endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import asyncio

from models import get_db
from schemas import OnboardingStatusResponse
from services.data_processing_coordinator import DataProcessingCoordinator
from services.database_service import DatabaseService

router = APIRouter()
coordinator = DataProcessingCoordinator()


@router.post("/process-data/{session_id}")
async def process_agent_data(
    session_id: int,
    website_url: Optional[str] = Form(None),
    pdf_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Process agent data - website scraping and/or PDF extraction
    """
    try:
        print(f"Processing data for session {session_id}")
        print(f"Website URL: {website_url}")
        print(f"PDF file: {pdf_file.filename if pdf_file else None}")
        
        # Validate inputs
        if not website_url and not pdf_file:
            raise HTTPException(status_code=400, detail="Either website_url or pdf_file must be provided")
        
        # Prepare PDF data if provided
        pdf_bytes = None
        pdf_filename = None
        if pdf_file:
            pdf_bytes = await pdf_file.read()
            pdf_filename = pdf_file.filename
        
        # Start async processing
        result = await coordinator.process_agent_data(
            session_id=session_id,
            website_url=website_url,
            pdf_bytes=pdf_bytes,
            pdf_filename=pdf_filename,
            db=db
        )
        
        return result
        
    except Exception as e:
        print(f"Process data error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process data: {str(e)}")


@router.post("/test-chromadb/{agent_id}")
async def test_chromadb_operations(agent_id: int):
    """Test ChromaDB operations for an agent"""
    try:
        from services.chromadb_service import ChromaDBService
        chromadb_service = ChromaDBService()
        
        # Test data
        test_documents = [
            {
                "content": "TechFlow Solutions is a leading provider of AI-powered SaaS tools for small businesses. We help companies streamline their operations with intelligent automation.",
                "source_type": "website",
                "source_url": "https://techflow.solutions/about",
                "chunk_index": 1
            },
            {
                "content": "Our main products include project management tools, CRM systems, and workflow automation. We serve small businesses with 5-50 employees.",
                "source_type": "website", 
                "source_url": "https://techflow.solutions/products",
                "chunk_index": 2
            }
        ]
        
        # Add documents
        success = chromadb_service.add_documents(agent_id, test_documents)
        
        if not success:
            return {"success": False, "error": "Failed to add documents"}
        
        # Test query
        results = chromadb_service.query_documents(agent_id, "What does TechFlow Solutions do?")
        
        # Get stats
        stats = chromadb_service.get_collection_stats(agent_id)
        
        return {
            "success": True,
            "documents_added": len(test_documents),
            "query_results": results,
            "collection_stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ChromaDB test failed: {str(e)}")


@router.get("/query-knowledge/{agent_id}")
async def query_agent_knowledge(agent_id: int, query: str, limit: int = 5):
    """Query agent's knowledge base"""
    try:
        from services.chromadb_service import ChromaDBService
        chromadb_service = ChromaDBService()
        
        results = chromadb_service.query_documents(agent_id, query, limit)
        
        return {
            "agent_id": agent_id,
            "query": query,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge query failed: {str(e)}")


@router.delete("/delete-knowledge/{agent_id}")
async def delete_agent_knowledge(agent_id: int):
    """Delete agent's entire knowledge collection"""
    try:
        from services.chromadb_service import ChromaDBService
        chromadb_service = ChromaDBService()
        
        success = chromadb_service.delete_agent_collection(agent_id)
        
        return {
            "success": success,
            "agent_id": agent_id,
            "message": "Knowledge collection deleted" if success else "Failed to delete collection"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge deletion failed: {str(e)}")
