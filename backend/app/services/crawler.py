"""
Crawler service using crawl4ai
"""
import logging
from typing import Dict, Any, List, Optional
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
                
                return {
                    "text": result.markdown or result.cleaned_html or "",
                    "html": result.html or "",
                    "url": url,
                    "success": result.success
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
                "success": False
            }
    
    async def crawl_with_depth(
        self, 
        start_url: str, 
        max_depth: int = 1, 
        current_depth: int = 0,
        max_results_per_depth: int = 10
    ) -> Dict[str, Any]:
        """
        Crawl a URL with depth control - crawls the page and optionally follows links
        
        Args:
            start_url: Starting URL to crawl
            max_depth: Maximum depth to crawl (0 = only start_url, 1 = start_url + 1 layer deep)
            current_depth: Current depth (used internally for recursion)
            max_results_per_depth: Maximum URLs to extract at each depth level
            
        Returns:
            Dictionary with:
            - 'content': Crawled content of the start_url
            - 'links': List of URLs found at depth 1 (if max_depth >= 1)
        """
        logger.info(f"Crawling depth {current_depth}: {start_url}")
        
        # Crawl the current URL
        content = await self.crawl_url(start_url, wait_for_content=(current_depth == 0))
        
        result = {
            "content": content,
            "links": [],
            "depth": current_depth
        }
        
        # If we haven't reached max depth, extract links and optionally crawl them
        if current_depth < max_depth and content.get("success"):
            html_content = content.get("html", "")
            if html_content:
                # Extract product URLs from the page using retailer handler
                links = self._extract_product_urls(html_content, start_url, max_results_per_depth)
                result["links"] = links
                logger.info(f"Found {len(links)} links at depth {current_depth}")
        
        return result
    
    def _extract_product_urls(self, html_content: str, base_url: str, max_results: int = 10) -> List[str]:
        """
        Extract product URLs from HTML content based on the retailer domain
        
        Args:
            html_content: HTML content to parse
            base_url: Base URL to resolve relative URLs
            max_results: Maximum number of URLs to return
            
        Returns:
            List of product URLs
        """
        # Get retailer handler for this URL
        retailer = get_retailer_handler(base_url)
        
        if retailer:
            # Use retailer-specific extraction logic
            return retailer.extract_product_urls(html_content, base_url, max_results)
        
        # Fallback: return empty list for unknown retailers
        logger.warning(f"No retailer handler found for {base_url}")
        return []
    
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
        
        # Use the new depth-based crawling method
        # max_depth=1 means: crawl listing page (depth 0) and extract links (depth 1)
        result = await self.crawl_with_depth(
            start_url=search_url,
            max_depth=1,  # Only go 1 layer deep (listing page + product links)
            current_depth=0,
            max_results_per_depth=max_results
        )
        
        # Return the links found at depth 1
        urls = result.get("links", [])
        logger.info(f"Extracted {len(urls)} URLs from {retailer} listing page")
        if urls:
            logger.debug(f"Sample URLs: {urls[:3]}")
        
        return urls

