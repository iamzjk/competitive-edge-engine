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
    
    @abstractmethod
    def extract_product_urls(self, html_content: str, base_url: str, max_results: int = 10) -> List[str]:
        """
        Extract product URLs from HTML content
        
        Args:
            html_content: HTML content to parse
            base_url: Base URL to resolve relative URLs
            max_results: Maximum number of URLs to return
            
        Returns:
            List of product URLs
        """
        pass
    
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

