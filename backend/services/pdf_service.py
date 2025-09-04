"""
PDF processing service for text extraction
"""
import os
from typing import Dict, Optional
from datetime import datetime
import PyPDF2
from io import BytesIO


class PDFService:
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Dict:
        """Extract text from PDF file"""
        try:
            print(f"Starting PDF text extraction for: {file_path}")
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                text_content = []
                total_pages = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():  # Only add non-empty pages
                            text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
                    except Exception as e:
                        print(f"Error extracting page {page_num + 1}: {e}")
                        continue
                
                combined_text = "\n\n".join(text_content)
                
                print(f"PDF extraction completed. {total_pages} pages, {len(combined_text)} characters")
                
                return {
                    "success": True,
                    "file_path": file_path,
                    "content": combined_text,
                    "total_pages": total_pages,
                    "total_characters": len(combined_text),
                    "extracted_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    @staticmethod
    def extract_text_from_upload(file_bytes: bytes, filename: str) -> Dict:
        """Extract text from uploaded PDF bytes"""
        try:
            print(f"Starting PDF text extraction for uploaded file: {filename}")
            
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
            
            text_content = []
            total_pages = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():  # Only add non-empty pages
                        text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
                except Exception as e:
                    print(f"Error extracting page {page_num + 1}: {e}")
                    continue
            
            combined_text = "\n\n".join(text_content)
            
            print(f"PDF extraction completed. {total_pages} pages, {len(combined_text)} characters")
            
            return {
                "success": True,
                "filename": filename,
                "content": combined_text,
                "total_pages": total_pages,
                "total_characters": len(combined_text),
                "extracted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }
