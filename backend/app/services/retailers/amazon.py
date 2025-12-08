"""
Amazon retailer-specific crawling logic
"""
import logging
import json
import re
import urllib.parse
from typing import List
from bs4 import BeautifulSoup
from crawl4ai import CrawlerRunConfig
from .base import BaseRetailer

logger = logging.getLogger(__name__)


class AmazonRetailer(BaseRetailer):
    """Amazon retailer implementation"""
    
    def build_search_url(self, query: str) -> str:
        """Build Amazon search URL"""
        return f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
    
    def is_product_page(self, url: str) -> bool:
        """Check if URL is an Amazon product page"""
        return "amazon.com" in url.lower() and ("/dp/" in url or "/gp/product/" in url)
    
    def get_crawl_config(self, url: str, wait_for_content: bool = False) -> CrawlerRunConfig:
        """Get crawl configuration for Amazon URLs"""
        is_product = self.is_product_page(url)
        
        if is_product:
            # For Amazon product pages, wait for specific elements to load
            return CrawlerRunConfig(
                wait_for="#productTitle, #feature-bullets, .a-section",
                page_timeout=90000,  # 90 seconds for Amazon product pages
                delay_before_return_html=3.0  # Wait 3 seconds after content loads
            )
        elif wait_for_content:
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
    
    def verify_product_content(self, html_content: str, url: str) -> bool:
        """Verify Amazon product page content"""
        if html_content and ("productTitle" in html_content or "product-title" in html_content.lower() or "About this item" in html_content):
            logger.info(f"Successfully crawled Amazon product page: {url}")
            return True
        else:
            logger.warning(f"Amazon product page may not have loaded correctly: {url}")
            return False
    
    def filter_product_urls(self, urls: List, base_url: str, max_results: int = 10) -> List[str]:
        """
        Filter and normalize Amazon product URLs from a list of URLs or URL dictionaries
        
        Handles:
        - Direct product links: /dp/[ASIN]/ in the path
        - Indirect/sponsored links: /sspa/click URLs with url= parameter containing encoded product link
        - Filters out non-product links: /deals, /b/ref=... without /dp/
        """
        base_domain = "/".join(base_url.split("/")[:3])
        seen_urls = set()
        product_urls = []
        
        def extract_asin_from_url(url_path: str) -> str:
            """Extract ASIN from a URL path containing /dp/[ASIN]/"""
            if '/dp/' not in url_path:
                return None
            parts = url_path.split('/dp/')
            if len(parts) > 1:
                asin = parts[1].split('/')[0].split('?')[0].split('#')[0]
                # Validate ASIN is 10 characters (alphanumeric)
                if asin and len(asin) == 10 and asin.isalnum():
                    return asin
            return None
        
        def is_non_product_link(href: str) -> bool:
            """Check if URL is a non-product link (deals, category pages, etc.)"""
            href_lower = href.lower()
            # Filter out deals pages, category pages, etc. that don't have /dp/
            if '/deals' in href_lower or '/b/ref=' in href_lower:
                if '/dp/' not in href_lower:
                    return True
            return False
        
        def normalize_product_url(asin: str) -> str:
            """Build clean product URL from ASIN"""
            return f"{base_domain}/dp/{asin}"
        
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
            
            # Skip non-product links (deals, category pages without /dp/)
            if is_non_product_link(url):
                continue
            
            # Handle /sspa/click URLs (sponsored/indirect links)
            if '/sspa/click' in url:
                try:
                    # Parse the URL to extract the url= parameter
                    parsed = urllib.parse.urlparse(url)
                    params = urllib.parse.parse_qs(parsed.query)
                    
                    # Look for url= parameter containing the product link
                    if 'url' in params and params['url']:
                        encoded_url = params['url'][0]
                        # Decode the URL
                        decoded_url = urllib.parse.unquote(encoded_url)
                        
                        # Check if decoded URL contains /dp/[ASIN]/
                        if '/dp/' in decoded_url:
                            asin = extract_asin_from_url(decoded_url)
                            if asin:
                                normalized_url = normalize_product_url(asin)
                                if normalized_url not in seen_urls:
                                    product_urls.append(normalized_url)
                                    seen_urls.add(normalized_url)
                                    if len(product_urls) >= max_results:
                                        break
                                    continue
                except Exception as e:
                    logger.debug(f"Error parsing /sspa/click URL: {e}")
                    continue
            
            # Handle direct /dp/ URLs
            if '/dp/' in url:
                asin = extract_asin_from_url(url)
                if asin:
                    normalized_url = normalize_product_url(asin)
                    if normalized_url not in seen_urls:
                        product_urls.append(normalized_url)
                        seen_urls.add(normalized_url)
                        if len(product_urls) >= max_results:
                            break
            # Handle /gp/product/ URLs
            elif '/gp/product/' in url:
                parts = url.split('/gp/product/')
                if len(parts) > 1:
                    product_id = parts[1].split('/')[0].split('?')[0].split('#')[0]
                    if product_id:
                        normalized_url = f"{base_domain}/gp/product/{product_id}"
                        if normalized_url not in seen_urls:
                            product_urls.append(normalized_url)
                            seen_urls.add(normalized_url)
                            if len(product_urls) >= max_results:
                                break
        
        return product_urls
    
    def extract_product_image(self, html_content: str, url: str) -> str:
        """Extract Amazon product image URL"""
        if not html_content:
            logger.warning(f"No HTML content provided for {url}")
            return ""
        
        logger.info(f"Extracting image from {url} (HTML length: {len(html_content)} chars)")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        base_domain = "/".join(url.split("/")[:3])
        
        # Try multiple Amazon image selectors
        selectors = [
            '#landingImage',  # Main product image
            '#imgBlkFront',   # Alternative main image
            '#main-image',     # Generic main image
            'img[data-a-image-name="landingImage"]',  # Data attribute selector
            '.a-dynamic-image[data-a-dynamic-image]',  # Dynamic image
            '#ebooks-img-canvas img',
            '#ebooks-img-canvas',
            '.a-dynamic-image img',
            '.a-dynamic-image',
            '[data-image-index="0"] img',
            '[data-image-index="0"]',
            '.image img',
            '.image',
            'img[alt*="Amazon"]',
            'img[alt*="generator"]',
            'img[alt*="inverter"]'
        ]
        
        for selector in selectors:
            img = soup.select_one(selector)
            if img:
                img_url = img.get('src') or img.get('data-src') or img.get('data-a-dynamic-image')
                if img_url:
                    # Parse data-a-dynamic-image if it's a JSON string
                    if img_url.startswith('{'):
                        try:
                            img_dict = json.loads(img_url)
                            if img_dict:
                                img_url = list(img_dict.keys())[0]
                        except:
                            pass
                    
                    # Handle relative URLs
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = base_domain + img_url
                    
                    # Clean up Amazon image URLs (remove size parameters but preserve file extension)
                    if 'amazon.com' in img_url:
                        # Remove size parameters like ._AC_SL1500_ but keep the file extension
                        if '._' in img_url:
                            # Split on ._ but try to preserve extension
                            parts = img_url.split('._')
                            base_url = parts[0]
                            # If base_url doesn't have an extension, try to find it in the original
                            if not any(base_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                                # Look for extension in the parts after ._
                                for part in parts[1:]:
                                    if any(part.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                                        # Extract just the extension
                                        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                                            if part.lower().endswith(ext):
                                                base_url = base_url + ext
                                                break
                                        break
                            img_url = base_url
                    
                    if img_url.startswith('http'):
                        logger.info(f"Extracted Amazon image URL: {img_url}")
                        return img_url
        
        logger.warning(f"No Amazon image found with selectors for {url}")
        
        # Last resort: look for any img tag with reasonable size
        all_imgs = soup.find_all('img')
        logger.info(f"Found {len(all_imgs)} total img tags on page")
        for img in all_imgs[:10]:  # Check first 10 images
            src = img.get('src') or img.get('data-src')
            alt = img.get('alt', '')
            if src and any(keyword in alt.lower() for keyword in ['generator', 'inverter', 'product', 'walmart', 'amazon', 'home depot']):
                logger.info(f"Found potential image with alt '{alt}': {src}")
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = base_domain + src
                if src.startswith('http'):
                    logger.info(f"Using fallback image: {src}")
                    return src
        
        return ""

