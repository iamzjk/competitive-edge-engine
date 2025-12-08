"""
Walmart retailer-specific crawling logic
"""
import logging
import urllib.parse
import re
from typing import List
from bs4 import BeautifulSoup
from crawl4ai import CrawlerRunConfig
from .base import BaseRetailer

logger = logging.getLogger(__name__)


class WalmartRetailer(BaseRetailer):
    """Walmart retailer implementation"""
    
    def build_search_url(self, query: str) -> str:
        """Build Walmart search URL"""
        return f"https://www.walmart.com/search?q={query.replace(' ', '+')}"
    
    def is_product_page(self, url: str) -> bool:
        """Check if URL is a Walmart product page"""
        return "walmart.com" in url.lower() and "/ip/" in url
    
    def get_crawl_config(self, url: str, wait_for_content: bool = False) -> CrawlerRunConfig:
        """Get crawl configuration for Walmart URLs"""
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
        """Filter and normalize Walmart product URLs from a list of URLs"""
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
            
            # Handle tracking URLs that contain product URLs in the 'rd' parameter
            if '/sp/track' in url and 'rd=' in url:
                try:
                    # Parse the tracking URL
                    parsed = urllib.parse.urlparse(url)
                    params = urllib.parse.parse_qs(parsed.query)
                    if 'rd' in params and params['rd']:
                        # Extract the redirect URL (URL encoded)
                        redirect_url = params['rd'][0]
                        # Decode the URL
                        decoded_url = urllib.parse.unquote(redirect_url)
                        # Check if it's a product URL
                        if '/ip/' in decoded_url and 'walmart.com' in decoded_url:
                            # Extract clean product URL
                            product_url = decoded_url.split('?')[0].split('#')[0]
                            if product_url not in seen_urls:
                                product_urls.append(product_url)
                                seen_urls.add(product_url)
                                if len(product_urls) >= max_results:
                                    break
                            continue
                except Exception as e:
                    logger.debug(f"Error parsing Walmart tracking URL: {e}")
                    continue
            
            # Handle direct /ip/ URLs
            if '/ip/' in url and 'walmart.com' in url:
                normalized_url = url.split('?')[0].split('#')[0]
                if normalized_url not in seen_urls:
                    product_urls.append(normalized_url)
                    seen_urls.add(normalized_url)
                    if len(product_urls) >= max_results:
                        break
        
        return product_urls
    
    def extract_product_image(self, html_content: str, url: str) -> str:
        """Extract Walmart product image URL"""
        if not html_content:
            logger.warning(f"No HTML content provided for {url}")
            return ""
        
        logger.info(f"Extracting image from {url} (HTML length: {len(html_content)} chars)")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        base_domain = "/".join(url.split("/")[:3])
        
        selectors = [
            '[data-testid="product-image"] img',
            '[data-testid="product-image"]',
            '.prod-hero-image img',
            '.prod-hero-image',
            'img[alt*="product"]',
            '.product-image img',
            '.product-image',
            '#main-image img',
            '#main-image',
            '.zoomable-image img',
            '.zoomable-image',
            'img[data-testid*="image"]',
            'img[alt*="Walmart"]',
            'img[alt*="generator"]',
            'img[alt*="inverter"]'
        ]
        
        for selector in selectors:
            img = soup.select_one(selector)
            if img:
                logger.info(f"Found Walmart image with selector: {selector}")
                img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-srcset') or img.get('data-original')
                if img_url:
                    # Handle srcset (multiple sizes)
                    if ' ' in img_url:
                        img_url = img_url.split(' ')[0]
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = base_domain + img_url
                    if img_url.startswith('http'):
                        logger.info(f"Extracted Walmart image URL: {img_url}")
                        return img_url
        
        logger.warning(f"No Walmart image found with selectors for {url}")
        
        # Fallback: Look for any img tag with walmart.com or i5.walmartimages.com in src
        logger.info("Trying fallback: searching for any img with walmart in src")
        all_imgs = soup.find_all('img')
        logger.info(f"Found {len(all_imgs)} total img tags on Walmart page")
        for img in all_imgs[:30]:  # Check first 30 images
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src and ('walmart' in src.lower() or 'walmartimages' in src.lower()):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = base_domain + src
                if src.startswith('http') and not any(skip in src.lower() for skip in ['logo', 'icon', 'sprite', 'badge', 'button']):
                    logger.info(f"Found Walmart image via fallback: {src}")
                    return src
        
        # Last resort: Look for any large image (likely product image)
        logger.info("Trying last resort: searching for largest image")
        largest_img = None
        largest_size = 0
        for img in all_imgs[:30]:
            src = img.get('src') or img.get('data-src')
            width = img.get('width')
            height = img.get('height')
            if src:
                try:
                    if width and height:
                        size = int(width) * int(height)
                        if size > largest_size and size > 10000:  # At least 100x100
                            largest_size = size
                            largest_img = src
                    elif 'walmartimages' in src.lower():
                        # Prefer walmartimages URLs
                        largest_img = src
                        break
                except:
                    pass
        
        if largest_img:
            if largest_img.startswith('//'):
                largest_img = 'https:' + largest_img
            elif largest_img.startswith('/'):
                largest_img = base_domain + largest_img
            if largest_img.startswith('http'):
                logger.info(f"Found largest image as fallback: {largest_img}")
                return largest_img
        
        return ""

