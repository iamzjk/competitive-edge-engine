"""
Lowes retailer-specific crawling logic
"""
import logging
import re
from typing import List
from bs4 import BeautifulSoup
from crawl4ai import CrawlerRunConfig
from .base import BaseRetailer

logger = logging.getLogger(__name__)


class LowesRetailer(BaseRetailer):
    """Lowes retailer implementation"""
    
    def build_search_url(self, query: str) -> str:
        """Build Lowes search URL"""
        return f"https://www.lowes.com/search?searchTerm={query.replace(' ', '+')}"
    
    def is_product_page(self, url: str) -> bool:
        """Check if URL is a Lowes product page"""
        return "lowes.com" in url.lower() and "/pd/" in url
    
    def get_crawl_config(self, url: str, wait_for_content: bool = False) -> CrawlerRunConfig:
        """Get crawl configuration for Lowes URLs"""
        if wait_for_content:
            # For search pages, wait longer for products to load
            return CrawlerRunConfig(
                wait_for="body",
                page_timeout=60000  # 60 seconds for search pages with dynamic content
            )
        else:
            return CrawlerRunConfig(
                wait_for="body",
                page_timeout=30000
            )
    
    def filter_product_urls(self, urls: List, base_url: str, max_results: int = 10) -> List[str]:
        """Filter and normalize Lowes product URLs from a list of URLs"""
        base_domain = "/".join(base_url.split("/")[:3])
        seen_urls = set()
        product_urls = []
        
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
            
            # Check if it's a product page (/pd/)
            if '/pd/' in url and 'lowes.com' in url:
                normalized_url = url.split('?')[0].split('#')[0]
                if normalized_url not in seen_urls:
                    product_urls.append(normalized_url)
                    seen_urls.add(normalized_url)
                    if len(product_urls) >= max_results:
                        break
        
        return product_urls
    
    def extract_product_image(self, html_content: str, url: str) -> str:
        """Extract Lowes product image URL"""
        if not html_content:
            logger.warning(f"No HTML content provided for {url}")
            return ""
        
        logger.info(f"Extracting image from {url} (HTML length: {len(html_content)} chars)")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        base_domain = "/".join(url.split("/")[:3])
        
        selectors = [
            '.product-image img',
            '[data-testid="product-image"] img',
            '.hero-image img',
            'img.product-hero-image'
        ]
        
        for selector in selectors:
            img = soup.select_one(selector)
            if img:
                img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if img_url:
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = base_domain + img_url
                    if img_url.startswith('http'):
                        return img_url
        
        return ""

