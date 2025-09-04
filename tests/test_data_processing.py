#!/usr/bin/env python3
"""
Test script for Tavily service directly
"""
import sys
import os
import asyncio

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.tavily_service import TavilyService

async def test_tavily_service():
    """Test the Tavily service directly"""
    tavily = TavilyService()
    
    print("Testing Tavily API key...")
    if tavily.test_api_key():
        print("✓ Tavily API key is working")
    else:
        print("✗ Tavily API key test failed")
        return
    
    print("\nTesting website scraping...")
    url = "https://www.7thgear.ai"
    print(f"Scraping: {url}")
    
    result = await tavily.scrape_website(url)
    
    print(f"\nScraping result:")
    print(f"Success: {result.get('success')}")
    print(f"URL: {result.get('url')}")
    print(f"Pages found: {result.get('pages_found', 0)}")
    print(f"Total characters: {result.get('total_characters', 0)}")
    
    if result.get('success'):
        content = result.get('content', '')
        print(f"\nFirst 500 characters of content:")
        print(content[:500] + "..." if len(content) > 500 else content)
    else:
        print(f"Error: {result.get('error')}")
        print(f"Raw response: {result.get('raw_response')}")

if __name__ == "__main__":
    asyncio.run(test_tavily_service())
