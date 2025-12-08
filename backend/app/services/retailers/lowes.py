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
    
    def extract_product_urls(self, html_content: str, base_url: str, max_results: int = 10) -> List[str]:
        """Extract Lowes product URLs from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        urls = []
        base_domain = "/".join(base_url.split("/")[:3])
        seen_urls = set()
        
        # Lowes: Look for /pd/ links (product detail pages)
        # Format: https://www.lowes.com/pd/Product-Name-Slug/ProductID
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/pd/' in href:
                if href.startswith('/pd/'):
                    # Extract /pd/Product-Name/ID format
                    url = base_domain + href.split('?')[0].split('#')[0]
                    if url not in seen_urls and '/pd/' in url:
                        urls.append(url)
                        seen_urls.add(url)
                elif 'lowes.com/pd/' in href:
                    url = href.split('?')[0].split('#')[0]
                    if url not in seen_urls:
                        urls.append(url)
                        seen_urls.add(url)
        
        # Fallback to regex if BeautifulSoup found nothing
        if not urls:
            pattern = r'href=["\']([^"\']*/pd/[^"\']*)'
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if match.startswith('http'):
                    url = match.split('?')[0].split('#')[0]
                else:
                    url = base_domain + match.split('?')[0].split('#')[0]
                if url not in seen_urls:
                    urls.append(url)
                    seen_urls.add(url)
        
        return urls[:max_results]
    
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

