#!/usr/bin/env python3
"""
Test script for complete async data processing with website + PDF
"""
import requests
import os

def test_complete_pipeline():
    """Test the complete async data processing pipeline"""
    
    # PDF file path
    pdf_path = r"C:\Users\ujwal\OneDrive\Documents\GitHub\Voice_platform\tests\test_pdf.pdf"
    
    print("Testing complete async data processing pipeline...")
    print(f"Website: https://www.7thgear.ai")
    print(f"PDF: {pdf_path}")
    
    # Check if PDF exists
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found at {pdf_path}")
        return

    try:
        # Step 1: Create onboarding session first
        print("\n🚀 Step 1: Creating onboarding session...")
        start_url = "http://127.0.0.1:8000/api/onboarding/start"
        start_response = requests.post(start_url, json={
            "initial_context": "Testing data processing pipeline with 7thgear.ai website and PDF resume"
        })
        
        print(f"Start session status: {start_response.status_code}")
        if start_response.status_code != 200:
            print(f"Failed to create session: {start_response.text}")
            return
            
        session_data = start_response.json()
        session_id = session_data["session_id"]
        agent_id = session_data["agent_id"]
        print(f"✅ Created session {session_id} for agent {agent_id}")
        
        # Step 2: Process data
        print(f"\n🚀 Step 2: Processing data for session {session_id}...")
        process_url = f"http://127.0.0.1:8000/api/data/process-data/{session_id}"
        # Prepare form data with website URL and PDF file
        with open(pdf_path, 'rb') as pdf_file:
            files = {
                'pdf_file': ('Plivo_resume-Spoo.pdf', pdf_file, 'application/pdf')
            }
            data = {
                'website_url': 'https://www.7thgear.ai'
            }
            
            print(f"\n� Starting async processing...")
            response = requests.post(process_url, files=files, data=data, timeout=120)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ SUCCESS!")
                print(f"Response: {result}")
                
                # Test querying the knowledge base
                if result.get('success'):
                    print("\n🔍 Testing knowledge base query...")
                    query_url = f"http://127.0.0.1:8000/api/data/query-knowledge/{agent_id}"
                    query_response = requests.get(
                        query_url, 
                        params={'query': 'What does 7thGear do?', 'limit': 3}
                    )
                    
                    if query_response.status_code == 200:
                        query_result = query_response.json()
                        print(f"Query Results: {len(query_result.get('results', []))} matches found")
                        
                        for i, match in enumerate(query_result.get('results', [])[:2]):
                            print(f"\nMatch {i+1}:")
                            print(f"Source: {match['metadata'].get('source_type')} - {match['metadata'].get('source_url', 'PDF')}")
                            print(f"Relevance: {match['relevance_score']:.3f}")
                            print(f"Content preview: {match['content'][:200]}...")
                    else:
                        print(f"Query failed: {query_response.status_code}")
                    
                    print("\n🔍 Testing knowledge base query 2...")
                    query_url = "http://127.0.0.1:8000/api/data/query-knowledge/1"
                    query_response = requests.get(
                        query_url, 
                        params={'query': 'What are the skills', 'limit': 3}
                    )
                    
                    if query_response.status_code == 200:
                        query_result = query_response.json()
                        print(f"Query Results: {len(query_result.get('results', []))} matches found")
                        
                        for i, match in enumerate(query_result.get('results', [])[:2]):
                            print(f"\nMatch {i+1}:")
                            print(f"Source: {match['metadata'].get('source_type')} - {match['metadata'].get('source_url', 'PDF')}")
                            print(f"Relevance: {match['relevance_score']:.3f}")
                            print(f"Content preview: {match['content'][:200]}...")
                    else:
                        print(f"Query failed: {query_response.status_code}")                
            else:
                print(f"❌ FAILED: {response.text}")
                
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_complete_pipeline()
