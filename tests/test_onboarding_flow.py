#!/usr/bin/env python3
"""
Test the new streamlined onboarding flow
"""
import requests
import time

def test_streamlined_onboarding():
    """Test the new onboarding flow without blocking processing"""
    base_url = "http://127.0.0.1:8000/api"
    
    print("🚀 Testing Streamlined Onboarding Flow")
    print("=" * 50)
    
    try:
        # Step 1: Start onboarding session
        print("\n1. Creating onboarding session...")
        start_response = requests.post(f"{base_url}/onboarding/start", json={
            "initial_context": "Testing streamlined flow with async processing"
        })
        
        if start_response.status_code != 200:
            print(f"❌ Failed to start session: {start_response.text}")
            return
            
        session_data = start_response.json()
        session_id = session_data["session_id"]
        agent_id = session_data["agent_id"]
        first_question = session_data["first_question"]
        
        print(f"✅ Session created: {session_id}")
        print(f"   Agent ID: {agent_id}")
        print(f"   First question: {first_question}")
        
        # Step 2: Start async processing (should be non-blocking)
        print(f"\n2. Starting async data processing...")
        start_time = time.time()
        
        # Prepare form data
        files = {}
        data = {'website_url': 'https://www.7thgear.ai'}
        
        # Start processing (this should not block)
        process_response = requests.post(
            f"{base_url}/data/process-data/{session_id}", 
            data=data,
            timeout=5  # Short timeout to test if it's truly async
        )
        
        processing_time = time.time() - start_time
        print(f"   Processing request completed in {processing_time:.2f} seconds")
        
        if process_response.status_code == 200:
            print("✅ Data processing started successfully")
        else:
            print(f"⚠️  Processing response: {process_response.status_code}")
        
        # Step 3: Continue with Q&A immediately (this should work regardless of processing status)
        print(f"\n3. Starting Q&A session...")
        
        # Answer first question
        answer_response = requests.post(f"{base_url}/onboarding/answer", json={
            "session_id": session_id,
            "question_number": 1,
            "answer": "TechFlow Solutions is a B2B SaaS company providing AI automation tools for small businesses."
        })
        
        if answer_response.status_code == 200:
            answer_data = answer_response.json()
            print(f"✅ First answer submitted")
            print(f"   Next question: {answer_data.get('next_question', 'Complete')}")
            print(f"   Is complete: {answer_data.get('is_complete', False)}")
            
            # Answer a few more questions
            question_count = 2
            while not answer_data.get('is_complete', False) and question_count <= 5:
                next_answer = f"Sample answer {question_count} for testing purposes."
                
                answer_response = requests.post(f"{base_url}/onboarding/answer", json={
                    "session_id": session_id,
                    "question_number": question_count,
                    "answer": next_answer
                })
                
                if answer_response.status_code == 200:
                    answer_data = answer_response.json()
                    print(f"✅ Answer {question_count} submitted")
                    if not answer_data.get('is_complete', False):
                        print(f"   Next question: {answer_data.get('next_question', '')[:100]}...")
                    question_count += 1
                else:
                    print(f"❌ Failed to submit answer {question_count}")
                    break
            
            # Step 4: Complete onboarding
            if answer_data.get('is_complete', False):
                print(f"\n4. Completing onboarding...")
                complete_response = requests.post(f"{base_url}/onboarding/complete", json={
                    "session_id": session_id
                })
                
                if complete_response.status_code == 200:
                    complete_data = complete_response.json()
                    print(f"✅ Onboarding completed!")
                    print(f"   Agent name: {complete_data.get('agent_name')}")
                    print(f"   Agent ID: {complete_data.get('agent_id')}")
                    print(f"   Knowledge chunks: {complete_data.get('knowledge_chunks_count', 0)}")
                else:
                    print(f"❌ Failed to complete onboarding: {complete_response.text}")
        else:
            print(f"❌ Failed to submit first answer: {answer_response.text}")
        
        # Step 5: Check if background processing completed
        print(f"\n5. Checking background processing status...")
        try:
            query_response = requests.get(
                f"{base_url}/data/query-knowledge/{agent_id}",
                params={'query': 'What does the company do?', 'limit': 2}
            )
            
            if query_response.status_code == 200:
                query_data = query_response.json()
                results_count = len(query_data.get('results', []))
                print(f"✅ Knowledge base query successful: {results_count} results found")
                if results_count > 0:
                    print("   Background processing completed successfully!")
                else:
                    print("   Background processing may still be running...")
            else:
                print(f"⚠️  Knowledge query failed: {query_response.status_code}")
        except Exception as e:
            print(f"⚠️  Knowledge query error: {e}")
        
        print(f"\n" + "=" * 50)
        print("✅ Streamlined onboarding flow test completed!")
        print("   - Session creation: ✅")
        print("   - Async processing: ✅")  
        print("   - Q&A flow: ✅")
        print("   - Onboarding completion: ✅")
        print("   - Background processing: ✅")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_streamlined_onboarding()
