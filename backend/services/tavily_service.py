"""
Tavily API service for web scraping
"""
import os
from tavily import TavilyClient
from typing import List, Dict, Optional
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

class TavilyService:
    def __init__(self):
        # Use your provided API key or environment variable
        api_key = os.getenv("TAVILY_API_KEY")
        self.client = TavilyClient(api_key)
    
    async def scrape_website(self, url: str, max_depth: int = 1, max_breadth: int = 1) -> Dict:
        """Scrape website content using Tavily crawl API with domain filtering"""
        try:
            print(f"Starting Tavily crawl for: {url}")
            
            # Extract domain from URL
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            if domain.startswith('www.'):
                domain = domain[4:]  # Remove www. prefix
            
            print(f"Filtering to domain: {domain}")
            
            # Use the crawl method with domain filtering and text format
            response = self.client.crawl(
                url=url,
                max_depth=max_depth,
                max_breadth=max_breadth,
                extract_depth="advanced",
                format="text",
                select_domains=[domain]
            )
            
            print(f"Tavily crawl response: {response}")
            
            # Process the crawl response
            if response and 'results' in response:
                all_content = []
                
                for result in response.get("results", []):
                    # Check if the result URL belongs to our target domain
                    result_domain = urlparse(result.get("url", "")).netloc
                    if result_domain.startswith('www.'):
                        result_domain = result_domain[4:]
                    
                    if result_domain == domain:
                        content_item = {
                            "url": result.get("url", url),
                            "title": result.get("title", ""),
                            "content": result.get("raw_content", ""),  # Use raw_content field from the actual response
                            "scraped_at": datetime.now().isoformat()
                        }
                        all_content.append(content_item)
                
                # Combine all content
                combined_content = "\n\n".join([
                    f"Page: {item['title']}\nURL: {item['url']}\n\n{item['content']}"
                    for item in all_content if item['content']
                ])
                
                print(f"Tavily crawl completed. Found {len(all_content)} pages from {domain}, {len(combined_content)} characters")
                
                return {
                    "success": True,
                    "url": url,
                    "domain": domain,
                    "content": combined_content,
                    "pages_found": len(all_content),
                    "total_characters": len(combined_content),
                    "scraped_at": datetime.now().isoformat(),
                    "raw_response": response
                }
            else:
                print(f"Tavily crawl returned no results: {response}")
                return {
                    "success": False,
                    "error": "No results returned from crawl",
                    "url": url,
                    "raw_response": response
                }
                
        except Exception as e:
            print(f"Tavily crawling error: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    def test_api_key(self) -> bool:
        """Test if Tavily API key is working"""
        try:
            # Test with a simple search query
            response = self.client.search(
                query="test",
                max_results=1
            )
            
            return response is not None
            
        except Exception as e:
            print(f"Tavily API test failed: {e}")
            return False
