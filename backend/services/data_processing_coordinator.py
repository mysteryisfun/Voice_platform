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
        Coordinate async processing of website and PDF data for an agent
        """
        try:
            print(f"Starting data processing for session {session_id}")
            
            # Get session and agent info
            session = DatabaseService.get_onboarding_session(db, session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            agent_id = session.agent_id
            
            # Update status to processing
            DatabaseService.update_processing_status(db, session_id, 
                                                   web_status="in_progress" if website_url else "skipped",
                                                   doc_status="in_progress" if (pdf_file_path or pdf_bytes) else "skipped")
            
            # Create async tasks
            tasks = []
            
            # Website scraping task
            if website_url:
                print(f"Adding website scraping task for: {website_url}")
                tasks.append(self._scrape_website(website_url, session_id, db))
            
            # PDF processing task  
            if pdf_file_path:
                print(f"Adding PDF processing task for: {pdf_file_path}")
                tasks.append(self._process_pdf_file(pdf_file_path, session_id, db))
            elif pdf_bytes and pdf_filename:
                print(f"Adding PDF processing task for uploaded: {pdf_filename}")
                tasks.append(self._process_pdf_bytes(pdf_bytes, pdf_filename, session_id, db))
            
            # Wait for all tasks to complete
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Collect successful results
                website_data = None
                pdf_data = None
                
                for result in results:
                    if isinstance(result, Exception):
                        print(f"Task failed with exception: {result}")
                        continue
                    
                    if result.get("type") == "website":
                        website_data = result.get("data")
                    elif result.get("type") == "pdf":
                        pdf_data = result.get("data")
                
                # Process and store in vector database
                return await self._store_in_vector_db(agent_id, session_id, website_data, pdf_data, db)
            
            else:
                return {"success": False, "error": "No content to process"}
                
        except Exception as e:
            print(f"Data processing error: {e}")
            # Update status to failed
            DatabaseService.update_processing_status(db, session_id,
                                                   web_status="failed",
                                                   doc_status="failed", 
                                                   vector_status="failed")
            return {"success": False, "error": str(e)}
    
    async def _scrape_website(self, url: str, session_id: int, db: Session) -> Dict:
        """Scrape website content"""
        try:
            result = await self.tavily_service.scrape_website(url)
            
            # Update status
            status = "completed" if result.get("success") else "failed"
            DatabaseService.update_processing_status(db, session_id, web_status=status)
            
            return {"type": "website", "data": result}
            
        except Exception as e:
            print(f"Website scraping error: {e}")
            DatabaseService.update_processing_status(db, session_id, web_status="failed")
            return {"type": "website", "data": {"success": False, "error": str(e)}}
    
    async def _process_pdf_file(self, file_path: str, session_id: int, db: Session) -> Dict:
        """Process PDF file"""
        try:
            # Run in executor since PDF processing is CPU-bound
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.pdf_service.extract_text_from_pdf, file_path
            )
            
            # Update status
            status = "completed" if result.get("success") else "failed"
            DatabaseService.update_processing_status(db, session_id, doc_status=status)
            
            return {"type": "pdf", "data": result}
            
        except Exception as e:
            print(f"PDF processing error: {e}")
            DatabaseService.update_processing_status(db, session_id, doc_status="failed")
            return {"type": "pdf", "data": {"success": False, "error": str(e)}}
    
    async def _process_pdf_bytes(self, pdf_bytes: bytes, filename: str, session_id: int, db: Session) -> Dict:
        """Process PDF from bytes"""
        try:
            # Run in executor since PDF processing is CPU-bound
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.pdf_service.extract_text_from_upload, pdf_bytes, filename
            )
            
            # Update status
            status = "completed" if result.get("success") else "failed"
            DatabaseService.update_processing_status(db, session_id, doc_status=status)
            
            return {"type": "pdf", "data": result}
            
        except Exception as e:
            print(f"PDF processing error: {e}")
            DatabaseService.update_processing_status(db, session_id, doc_status="failed")
            return {"type": "pdf", "data": {"success": False, "error": str(e)}}
    
    async def _store_in_vector_db(self, agent_id: int, session_id: int, 
                                 website_data: Optional[Dict], pdf_data: Optional[Dict], 
                                 db: Session) -> Dict:
        """Process content and store in ChromaDB"""
        try:
            print(f"Starting vector storage for agent {agent_id}")
            
            # Update status
            DatabaseService.update_processing_status(db, session_id, vector_status="in_progress")
            
            # Process content into chunks
            chunks = self.content_processor.combine_and_process(website_data, pdf_data)
            
            if not chunks:
                DatabaseService.update_processing_status(db, session_id, vector_status="failed")
                return {"success": False, "error": "No content chunks generated"}
            
            # Store in ChromaDB with SQLite tracking
            success = self.chromadb_service.add_documents(agent_id, chunks, db)
            
            if success:
                # Update status
                DatabaseService.update_processing_status(db, session_id, vector_status="completed")
                
                # Get collection stats
                stats = self.chromadb_service.get_collection_stats(agent_id)
                
                return {
                    "success": True,
                    "agent_id": agent_id,
                    "chunks_processed": len(chunks),
                    "vector_stats": stats,
                    "website_processed": website_data is not None and website_data.get("success", False),
                    "pdf_processed": pdf_data is not None and pdf_data.get("success", False)
                }
            else:
                DatabaseService.update_processing_status(db, session_id, vector_status="failed")
                return {"success": False, "error": "Failed to store in vector database"}
                
        except Exception as e:
            print(f"Vector storage error: {e}")
            DatabaseService.update_processing_status(db, session_id, vector_status="failed")
            return {"success": False, "error": str(e)}
