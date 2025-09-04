"""
Content processing service for chunking and embedding
"""
import re
from typing import List, Dict, Any
from datetime import datetime


class ContentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\'\/\@\#\$\%\&\*\+\=]', '', text)
        
        # Remove multiple consecutive punctuation
        text = re.sub(r'([.!?]){2,}', r'\1', text)
        
        return text.strip()
    
    def chunk_text(self, text: str, source_type: str, source_url: str = "") -> List[Dict[str, Any]]:
        """Split text into chunks with metadata"""
        cleaned_text = self.clean_text(text)
        
        # Simple sentence-based chunking
        sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 1
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size, save current chunk
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunks.append({
                    "content": current_chunk.strip(),
                    "source_type": source_type,
                    "source_url": source_url,
                    "chunk_index": chunk_index,
                    "chunk_size": len(current_chunk),
                    "created_at": datetime.now().isoformat()
                })
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
                chunk_index += 1
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk if it has content
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "source_type": source_type,
                "source_url": source_url,
                "chunk_index": chunk_index,
                "chunk_size": len(current_chunk),
                "created_at": datetime.now().isoformat()
            })
        
        print(f"Text chunked into {len(chunks)} pieces for {source_type}")
        return chunks
    
    def process_website_content(self, website_data: Dict) -> List[Dict[str, Any]]:
        """Process website scraping results into chunks"""
        if not website_data.get("success") or not website_data.get("content"):
            return []
        
        return self.chunk_text(
            text=website_data["content"],
            source_type="website",
            source_url=website_data.get("url", "")
        )
    
    def process_pdf_content(self, pdf_data: Dict, filename: str = "") -> List[Dict[str, Any]]:
        """Process PDF extraction results into chunks"""
        if not pdf_data.get("success") or not pdf_data.get("content"):
            return []
        
        return self.chunk_text(
            text=pdf_data["content"],
            source_type="pdf",
            source_url=f"file://{filename or pdf_data.get('filename', 'uploaded.pdf')}"
        )
    
    def combine_and_process(self, website_data: Dict = None, pdf_data: Dict = None) -> List[Dict[str, Any]]:
        """Combine website and PDF content, then chunk everything"""
        all_chunks = []
        
        # Process website content
        if website_data:
            website_chunks = self.process_website_content(website_data)
            all_chunks.extend(website_chunks)
        
        # Process PDF content  
        if pdf_data:
            pdf_chunks = self.process_pdf_content(pdf_data)
            all_chunks.extend(pdf_chunks)
        
        # Re-index chunks sequentially
        for i, chunk in enumerate(all_chunks):
            chunk["chunk_index"] = i + 1
        
        print(f"Total content processed into {len(all_chunks)} chunks")
        return all_chunks
