"""
Crawler service using crawl4ai
"""
import logging
from typing import Dict, Any, List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from app.config import settings
from app.services.retailers import get_retailer_handler

logger = logging.getLogger(__name__)


class CrawlerService:
    """Service for crawling web pages"""
    
    def __init__(self):
        self.browser_type = settings.CRAWL4AI_BROWSER_TYPE
    
    async def crawl_url(self, url: str, wait_for_content: bool = False) -> Dict[str, Any]:
        """
        Crawl a URL and return extracted content
        
        Args:
            url: URL to crawl
            wait_for_content: If True, wait longer for dynamic content to load
            
        Returns:
            Dictionary with crawled content (text, html, etc.)
        """
        browser_config = BrowserConfig(
            browser_type=self.browser_type,
            headless=True
        )
        
        # Get retailer handler for this URL
        retailer = get_retailer_handler(url)
        
        # Get crawl configuration from retailer or use default
        if retailer:
            crawler_config = retailer.get_crawl_config(url, wait_for_content)
        else:
            # Default config for unknown retailers
            if wait_for_content:
                crawler_config = CrawlerRunConfig(
                    wait_for="body",
                    page_timeout=60000
                )
            else:
                crawler_config = CrawlerRunConfig(
                    wait_for="body",
                    page_timeout=30000
                )
        
        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(
                    url=url,
                    config=crawler_config
                )
                
                # Verify product content if retailer handler exists
                if retailer and result.success:
                    html = result.html or ""
                    if retailer.is_product_page(url):
                        retailer.verify_product_content(html, url)
                
                # Extract internal links from crawl result
                internal_links = []
                if hasattr(result, 'links') and result.links:
                    internal_links = result.links.get('internal', [])
                
                return {
                    "text": result.markdown or result.cleaned_html or "",
                    "html": result.html or "",
                    "url": url,
                    "success": result.success,
                    "links": {
                        "internal": internal_links
                    }
                }
        except Exception as e:
            # Handle browser closure and other errors gracefully
            error_msg = str(e)
            if "closed" in error_msg.lower() or "epipe" in error_msg.lower():
                logger.warning(f"Browser closed unexpectedly while crawling {url}: {e}")
            else:
                logger.error(f"Error crawling {url}: {e}")
            
            return {
                "text": "",
                "html": "",
                "url": url,
                "success": False,
                "links": {
                    "internal": []
                }
            }
    
    def extract_product_image(self, html_content: str, url: str) -> str:
        """
        Extract the main product image URL from HTML content
        
        Args:
            html_content: HTML content to parse
            url: Base URL to resolve relative image URLs
            
        Returns:
            Product image URL or empty string if not found
        """
        # Get retailer handler for this URL
        retailer = get_retailer_handler(url)
        
        if retailer:
            # Use retailer-specific image extraction logic
            return retailer.extract_product_image(html_content, url)
        
        # Fallback: return empty string for unknown retailers
        logger.warning(f"No retailer handler found for {url}, cannot extract image")
        return ""
    
    async def search_retailer(self, retailer: str, query: str, max_results: int = 10) -> List[str]:
        """
        Search a retailer site for products
        
        Args:
            retailer: Retailer name (amazon, homedepot, walmart, lowes)
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of product URLs
        """
        # Get retailer handler
        retailer_handler = get_retailer_handler(retailer)
        
        if not retailer_handler:
            logger.warning(f"Unknown retailer: {retailer}")
            return []
        
        # Build search URL using retailer handler
        search_url = retailer_handler.build_search_url(query)
        
        # Crawl the search page
        logger.info(f"Crawling search page: {search_url}")
        content = await self.crawl_url(search_url, wait_for_content=True)
        
        if not content.get("success"):
            logger.warning(f"Failed to crawl search page: {search_url}")
            return []
        
        # Get internal links from crawl result
        internal_links = content.get("links", {}).get("internal", [])
        if not internal_links:
            logger.warning(f"No internal links found from search page: {search_url}")
            return []
        
        logger.info(f"Found {len(internal_links)} internal links from {retailer} search page")
        
        # Filter product URLs from internal links using retailer handler
        urls = retailer_handler.filter_product_urls(internal_links, search_url, max_results)
        logger.info(f"Filtered to {len(urls)} product URLs from {retailer} listing page")
        if urls:
            logger.debug(f"Sample URLs: {urls[:3]}")
        
        return urls

