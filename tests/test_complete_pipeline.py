#!/usr/bin/env python3
"""
Test script for complete async data processing pipeline
"""
import requests
import asyncio
import sys
import os

# Add backend to path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_tavily_service():
    """Test Tavily service directly"""
    from services.tavily_service import TavilyService
    
    print("=== Testing Tavily Service Directly ===")
    tavily = TavilyService()
    
    result = await tavily.scrape_website("https://www.7thgear.ai")
    
    print(f"Success: {result['success']}")
    print(f"Domain: {result.get('domain', 'N/A')}")
    print(f"Pages found: {result.get('pages_found', 0)}")
    print(f"Content length: {result.get('total_characters', 0)} characters")
    
    if result['success'] and result.get('content'):
        print(f"First 500 chars of content: {result['content'][:500]}...")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    return result

def test_api_endpoint():
    """Test the API endpoint for data processing"""
    print("\n=== Testing API Endpoint ===")
    url = "http://127.0.0.1:8000/api/data/process-data/1"
    
    # Test with website URL
    data = {
        'website_url': 'https://www.7thgear.ai'
    }
    
    print("Testing complete async data processing pipeline...")
    print(f"URL: {url}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(url, data=data)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Success: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"Documents processed: {result.get('documents_processed', 0)}")
            print(f"Content chunks: {result.get('chunks_created', 0)}")
            print(f"Stored in ChromaDB: {result.get('chromadb_success', False)}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_chromadb_query():
    """Test querying the stored data"""
    print("\n=== Testing ChromaDB Query ===")
    url = "http://127.0.0.1:8000/api/data/query-knowledge/1"
    
    params = {
        'query': 'What does 7th Gear do?',
        'limit': 3
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        print(f"Query: {result.get('query')}")
        print(f"Results found: {result.get('total_results', 0)}")
        
        for i, res in enumerate(result.get('results', [])[:2]):
            print(f"\nResult {i+1}:")
            print(f"Relevance: {res.get('relevance_score', 0):.3f}")
            print(f"Content: {res.get('content', '')[:200]}...")
            
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None

async def main():
    """Run all tests"""
    print("Testing Voice Agent Platform - Async Data Processing")
    print("=" * 50)
    
    # Test Tavily service first
    tavily_result = await test_tavily_service()
    
    # Test API endpoint
    api_result = test_api_endpoint()
    
    # Test querying stored data
    query_result = test_chromadb_query()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Tavily Service: {'✅ SUCCESS' if tavily_result.get('success') else '❌ FAILED'}")
    print(f"API Endpoint: {'✅ SUCCESS' if api_result and api_result.get('success') else '❌ FAILED'}")
    print(f"ChromaDB Query: {'✅ SUCCESS' if query_result and query_result.get('total_results', 0) > 0 else '❌ FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())
