"""
Amazon retailer-specific crawling logic
"""
import logging
import json
import re
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
    
    def extract_product_urls(self, html_content: str, base_url: str, max_results: int = 10) -> List[str]:
        """Extract Amazon product URLs from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        urls = []
        base_domain = "/".join(base_url.split("/")[:3])
        seen_urls = set()
        
        # Amazon: Look for /dp/ and /gp/product/ links
        # Format: /Product-Name-Slug/dp/ASIN/ref=... (relative URLs from search pages)
        # ASINs are 10 characters (alphanumeric)
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            if not href:
                continue
            
            # Handle relative URLs (common in search results)
            if href.startswith('/') and ('/dp/' in href or '/gp/product/' in href):
                if '/dp/' in href:
                    # Extract ASIN from /Product-Name/dp/ASIN or /dp/ASIN
                    parts = href.split('/dp/')
                    if len(parts) > 1:
                        asin = parts[1].split('/')[0].split('?')[0].split('#')[0]
                        # Validate ASIN is 10 characters (alphanumeric)
                        if asin and len(asin) == 10 and asin.isalnum():
                            # Build clean URL: amazon.com/dp/ASIN
                            url = f"{base_domain}/dp/{asin}"
                            if url not in seen_urls:
                                urls.append(url)
                                seen_urls.add(url)
                elif '/gp/product/' in href:
                    # Extract product ID from /gp/product/ID
                    parts = href.split('/gp/product/')
                    if len(parts) > 1:
                        product_id = parts[1].split('/')[0].split('?')[0].split('#')[0]
                        if product_id:
                            url = f"{base_domain}/gp/product/{product_id}"
                            if url not in seen_urls:
                                urls.append(url)
                                seen_urls.add(url)
            # Handle absolute URLs
            elif href.startswith('http') and 'amazon.com' in href and ('/dp/' in href or '/gp/product/' in href):
                if '/dp/' in href:
                    parts = href.split('/dp/')
                    if len(parts) > 1:
                        asin = parts[1].split('/')[0].split('?')[0].split('#')[0]
                        if asin and len(asin) == 10 and asin.isalnum():
                            url = f"{base_domain}/dp/{asin}"
                            if url not in seen_urls:
                                urls.append(url)
                                seen_urls.add(url)
                elif '/gp/product/' in href:
                    parts = href.split('/gp/product/')
                    if len(parts) > 1:
                        product_id = parts[1].split('/')[0].split('?')[0].split('#')[0]
                        if product_id:
                            url = f"{base_domain}/gp/product/{product_id}"
                            if url not in seen_urls:
                                urls.append(url)
                                seen_urls.add(url)
        
        # Fallback to regex if BeautifulSoup found nothing
        if not urls:
            pattern = r'href=["\']([^"\']*/(?:dp|gp/product)/[A-Z0-9]{10}[^"\']*)'
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

