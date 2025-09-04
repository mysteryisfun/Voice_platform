"""
Async data processing coordinator
"""
import asyncio
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from datetime import datetime

from services.tavily_service import TavilyService
from services.pdf_service import PDFService
from services.content_processor import ContentProcessor
from services.chromadb_service import ChromaDBService
from services.database_service import DatabaseService


class DataProcessingCoordinator:
    def __init__(self):
        self.tavily_service = TavilyService()
        self.pdf_service = PDFService()
        self.content_processor = ContentProcessor()
        self.chromadb_service = ChromaDBService()
    
    async def process_agent_data(self, session_id: int, website_url: Optional[str] = None, 
                                pdf_file_path: Optional[str] = None, pdf_bytes: Optional[bytes] = None,
                                pdf_filename: Optional[str] = None, db: Session = None) -> Dict:
        """
        Coordinate async processing of website and PDF data for an agent - FIRE AND FORGET
        """
        try:
            print(f"Starting FIRE-AND-FORGET data processing for session {session_id}")
            
            # Get session and agent info
            session = DatabaseService.get_onboarding_session(db, session_id)
            if not session:
                print(f"Session {session_id} not found")
                return {"success": False, "error": "Session not found"}
            
            agent_id = session.agent_id
            print(f"Processing data for agent {agent_id}")
            
            # Update status to processing
            DatabaseService.update_processing_status(db, session_id, 
                                                   web_status="in_progress" if website_url else "skipped",
                                                   doc_status="in_progress" if (pdf_file_path or pdf_bytes) else "skipped")
            
            # Start individual tasks WITHOUT WAITING FOR THEM
            if website_url:
                print(f"Starting website scraping for: {website_url}")
                asyncio.create_task(self._scrape_website_fire_and_forget(website_url, agent_id, session_id, db))
            
            if pdf_file_path:
                print(f"Starting PDF processing for: {pdf_file_path}")
                asyncio.create_task(self._process_pdf_file_fire_and_forget(pdf_file_path, agent_id, session_id, db))
            elif pdf_bytes and pdf_filename:
                print(f"Starting PDF processing for uploaded: {pdf_filename}")
                asyncio.create_task(self._process_pdf_bytes_fire_and_forget(pdf_bytes, pdf_filename, agent_id, session_id, db))
            
            # Return immediately - don't wait for anything
            print(f"All background tasks started for session {session_id}")
            return {
                "success": True,
                "message": "Background processing started",
                "session_id": session_id,
                "agent_id": agent_id
            }
                
        except Exception as e:
            print(f"Data processing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _scrape_website_fire_and_forget(self, url: str, agent_id: int, session_id: int, db: Session):
        """Scrape website content in background"""
        try:
            print(f"BACKGROUND: Starting website scraping for {url}")
            result = await self.tavily_service.scrape_website(url)
            
            # Update status
            status = "completed" if result.get("success") else "failed"
            DatabaseService.update_processing_status(db, session_id, web_status=status)
            
            if result.get("success"):
                # Process and store immediately
                chunks = self.content_processor.process_website_content(result)
                if chunks:
                    self.chromadb_service.add_documents(agent_id, chunks, db)
                    print(f"BACKGROUND: Website processing completed for session {session_id}")
            
        except Exception as e:
            print(f"BACKGROUND: Website scraping error: {e}")
            DatabaseService.update_processing_status(db, session_id, web_status="failed")
    
    async def _process_pdf_file_fire_and_forget(self, file_path: str, agent_id: int, session_id: int, db: Session):
        """Process PDF file in background"""
        try:
            print(f"BACKGROUND: Starting PDF processing for {file_path}")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.pdf_service.extract_text_from_pdf, file_path
            )
            
            # Update status
            status = "completed" if result.get("success") else "failed"
            DatabaseService.update_processing_status(db, session_id, doc_status=status)
            
            if result.get("success"):
                # Process and store immediately
                chunks = self.content_processor.process_pdf_content(result)
                if chunks:
                    self.chromadb_service.add_documents(agent_id, chunks, db)
                    print(f"BACKGROUND: PDF processing completed for session {session_id}")
            
        except Exception as e:
            print(f"BACKGROUND: PDF processing error: {e}")
            DatabaseService.update_processing_status(db, session_id, doc_status="failed")
    
    async def _process_pdf_bytes_fire_and_forget(self, pdf_bytes: bytes, filename: str, agent_id: int, session_id: int, db: Session):
        """Process PDF from bytes in background"""
        try:
            print(f"BACKGROUND: Starting PDF processing for uploaded {filename}")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.pdf_service.extract_text_from_upload, pdf_bytes, filename
            )
            
            # Update status
            status = "completed" if result.get("success") else "failed"
            DatabaseService.update_processing_status(db, session_id, doc_status=status)
            
            if result.get("success"):
                # Process and store immediately
                chunks = self.content_processor.process_pdf_content(result, filename)
                if chunks:
                    self.chromadb_service.add_documents(agent_id, chunks, db)
                    print(f"BACKGROUND: PDF processing completed for session {session_id}")
            
        except Exception as e:
            print(f"BACKGROUND: PDF processing error: {e}")
            DatabaseService.update_processing_status(db, session_id, doc_status="failed")
