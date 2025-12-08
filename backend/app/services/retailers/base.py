"""
Base abstract class for retailer-specific crawling logic
"""
from abc import ABC, abstractmethod
from typing import List
from crawl4ai import CrawlerRunConfig


class BaseRetailer(ABC):
    """Abstract base class for retailer-specific crawling logic"""
    
    @abstractmethod
    def build_search_url(self, query: str) -> str:
        """
        Build search URL for the retailer
        
        Args:
            query: Search query string
            
        Returns:
            Complete search URL
        """
        pass
    
    def filter_product_urls(self, urls: List, base_url: str, max_results: int = 10) -> List[str]:
        """
        Filter and normalize product URLs from a list of URLs or URL dictionaries
        
        Args:
            urls: List of URLs (strings) or URL dictionaries (from crawl4ai with 'href' key)
            base_url: Base URL to resolve relative URLs
            max_results: Maximum number of URLs to return
            
        Returns:
            List of filtered product URLs
        """
        # Default implementation: filter URLs that are product pages
        product_urls = []
        seen_urls = set()
        base_domain = "/".join(base_url.split("/")[:3])
        
        for url_item in urls:
            # Extract href if it's a dictionary (from crawl4ai)
            if isinstance(url_item, dict):
                url = url_item.get('href', '')
            elif isinstance(url_item, str):
                url = url_item
            else:
                continue
            
            if not url:
                continue
            
            # Resolve relative URLs
            if url.startswith('/'):
                url = base_domain + url
            elif not url.startswith('http'):
                continue
            
            # Check if it's a product page
            if self.is_product_page(url):
                # Normalize URL (remove query params, fragments, etc.)
                normalized = self._normalize_product_url(url)
                if normalized and normalized not in seen_urls:
                    product_urls.append(normalized)
                    seen_urls.add(normalized)
                    if len(product_urls) >= max_results:
                        break
        
        return product_urls
    
    def _normalize_product_url(self, url: str) -> str:
        """
        Normalize a product URL to a clean format
        
        Args:
            url: Product URL to normalize
            
        Returns:
            Normalized product URL
        """
        # Default implementation: remove query params and fragments
        return url.split('?')[0].split('#')[0]
    
    @abstractmethod
    def extract_product_image(self, html_content: str, url: str) -> str:
        """
        Extract the main product image URL from HTML content
        
        Args:
            html_content: HTML content to parse
            url: Base URL to resolve relative image URLs
            
        Returns:
            Product image URL or empty string if not found
        """
        pass
    
    @abstractmethod
    def get_crawl_config(self, url: str, wait_for_content: bool = False) -> CrawlerRunConfig:
        """
        Get crawl configuration for a URL
        
        Args:
            url: URL to crawl
            wait_for_content: If True, wait longer for dynamic content to load
            
        Returns:
            CrawlerRunConfig instance
        """
        pass
    
    @abstractmethod
    def is_product_page(self, url: str) -> bool:
        """
        Check if URL is a product page
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is a product page, False otherwise
        """
        pass
    
    def verify_product_content(self, html_content: str, url: str) -> bool:
        """
        Verify that crawled content is actually a product page
        (not a captcha, error page, etc.)
        
        Args:
            html_content: HTML content to verify
            url: URL that was crawled
            
        Returns:
            True if content appears to be a valid product page
        """
        # Default implementation - can be overridden by subclasses
        return True

