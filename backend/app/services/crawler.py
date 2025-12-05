"""
Crawler service using crawl4ai
"""
from typing import Dict, Any
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from app.config import settings


class CrawlerService:
    """Service for crawling web pages"""
    
    def __init__(self):
        self.browser_type = settings.CRAWL4AI_BROWSER_TYPE
    
    async def crawl_url(self, url: str) -> Dict[str, Any]:
        """
        Crawl a URL and return extracted content
        
        Args:
            url: URL to crawl
            
        Returns:
            Dictionary with crawled content (text, html, etc.)
        """
        browser_config = BrowserConfig(
            browser_type=self.browser_type,
            headless=True
        )
        
        crawler_config = CrawlerRunConfig(
            wait_for="body",
            page_timeout=30000
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url=url,
                config=crawler_config
            )
            
            return {
                "text": result.markdown or result.cleaned_html or "",
                "html": result.html or "",
                "url": url,
                "success": result.success
            }
    
    async def search_retailer(self, retailer: str, query: str, max_results: int = 10) -> list:
        """
        Search a retailer site for products
        
        Args:
            retailer: Retailer name (amazon, homedepot, walmart, lowes)
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of product URLs
        """
        # Build search URL based on retailer
        search_urls = {
            "amazon": f"https://www.amazon.com/s?k={query.replace(' ', '+')}",
            "homedepot": f"https://www.homedepot.com/s/{query.replace(' ', '%20')}",
            "walmart": f"https://www.walmart.com/search?q={query.replace(' ', '+')}",
            "lowes": f"https://www.lowes.com/search?searchTerm={query.replace(' ', '+')}"
        }
        
        if retailer.lower() not in search_urls:
            return []
        
        search_url = search_urls[retailer.lower()]
        
        # Crawl search page
        content = await self.crawl_url(search_url)
        
        # Extract product URLs from search results
        # This is a simplified implementation
        # In production, you would use retailer-specific selectors
        
        import re
        urls = []
        
        # Simple regex to find product URLs in HTML
        # This is a basic implementation - production would need more sophisticated parsing
        html_content = content.get("html", "")
        
        # Look for common product URL patterns
        if "amazon.com" in search_url:
            # Amazon product URLs
            pattern = r'href="(/dp/[A-Z0-9]+|/gp/product/[A-Z0-9]+)'
        elif "homedepot.com" in search_url:
            # Home Depot product URLs
            pattern = r'href="(/p/[^"]+)"'
        elif "walmart.com" in search_url:
            # Walmart product URLs
            pattern = r'href="(/ip/[^"]+)"'
        elif "lowes.com" in search_url:
            # Lowes product URLs
            pattern = r'href="(/p/[^"]+)"'
        else:
            return []
        
        matches = re.findall(pattern, html_content)
        
        # Convert relative URLs to absolute
        base_url = "/".join(search_url.split("/")[:3])
        for match in matches[:max_results]:
            if match.startswith("http"):
                urls.append(match)
            else:
                urls.append(base_url + match)
        
        return urls

