"""
Crawler service using crawl4ai
"""
import logging
from typing import Dict, Any, List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from bs4 import BeautifulSoup
from app.config import settings

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
        
        # Determine if this is an Amazon product page
        is_amazon_product = "amazon.com" in url and ("/dp/" in url or "/gp/product/" in url)
        
        # For Amazon product pages, wait for specific elements to load
        if is_amazon_product:
            # Wait for product title or product details to appear
            # Amazon product pages have these common selectors:
            # - #productTitle (product title)
            # - #feature-bullets (product features)
            # - .a-section (product details sections)
            crawler_config = CrawlerRunConfig(
                wait_for="#productTitle, #feature-bullets, .a-section",
                page_timeout=90000,  # 90 seconds for Amazon product pages
                delay_before_return_html=3.0  # Wait 3 seconds after content loads
            )
        elif wait_for_content:
        # For search pages, wait longer for products to load
            crawler_config = CrawlerRunConfig(
                wait_for="body",
                page_timeout=60000  # 60 seconds for search pages with dynamic content
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
                
                # For Amazon product pages, verify we got useful content
                if is_amazon_product and result.success:
                    html = result.html or ""
                    # Check if we got actual product content (not a captcha or error page)
                    if html and ("productTitle" in html or "product-title" in html.lower() or "About this item" in html):
                        logger.info(f"Successfully crawled Amazon product page: {url}")
                    else:
                        logger.warning(f"Amazon product page may not have loaded correctly: {url}")
                        # Still return the content, but log the warning
                
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
                # Extract product URLs from the page
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
        soup = BeautifulSoup(html_content, 'html.parser')
        urls = []
        base_domain = "/".join(base_url.split("/")[:3])
        seen_urls = set()
        
        # Determine retailer from base URL
        if "amazon.com" in base_url:
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
        
        elif "homedepot.com" in base_url:
            # Home Depot: Look for /p/ links
            # Format: https://www.homedepot.com/p/Product-Name-Slug/ProductID
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/p/' in href:
                    if href.startswith('/p/'):
                        url = base_domain + href.split('?')[0]
                        if url not in seen_urls and '/p/' in url:
                            urls.append(url)
                            seen_urls.add(url)
                    elif 'homedepot.com/p/' in href:
                        url = href.split('?')[0]
                        if url not in seen_urls:
                            urls.append(url)
                            seen_urls.add(url)
        
        elif "walmart.com" in base_url:
            # Walmart: Look for /ip/ links
            # Format: /ip/Product-Name-Slug/ProductID?query-params (relative URLs)
            # Also handles tracking URLs: /sp/track?...&rd=https%3A%2F%2Fwww.walmart.com%2Fip%2F...
            import urllib.parse
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').strip()
                if not href:
                    continue
                
                # Handle direct /ip/ links (relative or absolute)
                if '/ip/' in href:
                    if href.startswith('/ip/'):
                        # Relative URL: /ip/Product-Name/ID
                        url = base_domain + href.split('?')[0].split('#')[0]
                        if url not in seen_urls and '/ip/' in url:
                            urls.append(url)
                            seen_urls.add(url)
                    elif 'walmart.com/ip/' in href:
                        # Absolute URL, remove query params and fragments
                        url = href.split('?')[0].split('#')[0]
                        if url not in seen_urls:
                            urls.append(url)
                            seen_urls.add(url)
                
                # Handle tracking URLs that contain product URLs in the 'rd' parameter
                elif '/sp/track' in href and 'rd=' in href:
                    try:
                        # Parse the tracking URL
                        parsed = urllib.parse.urlparse(href)
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
                                    urls.append(product_url)
                                    seen_urls.add(product_url)
                    except Exception as e:
                        logger.debug(f"Error parsing Walmart tracking URL: {e}")
                        continue
        
        elif "lowes.com" in base_url:
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
            import re
            patterns = {
                "amazon.com": r'href=["\']([^"\']*/(?:dp|gp/product)/[A-Z0-9]{10}[^"\']*)',
                "homedepot.com": r'href=["\']([^"\']*/p/[^"\']*)',
                "walmart.com": r'href=["\']([^"\']*/ip/[^"\']*)',
                "lowes.com": r'href=["\']([^"\']*/pd/[^"\']*)'
            }
            
            for domain, pattern in patterns.items():
                if domain in base_url:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    for match in matches:
                        if match.startswith('http'):
                            url = match.split('?')[0].split('#')[0]
                        else:
                            url = base_domain + match.split('?')[0].split('#')[0]
                        if url not in seen_urls:
                            urls.append(url)
                            seen_urls.add(url)
                    break
        
        return urls[:max_results]
    
    def extract_product_image(self, html_content: str, url: str) -> str:
        """
        Extract the main product image URL from HTML content
        
        Args:
            html_content: HTML content to parse
            url: Base URL to resolve relative image URLs
            
        Returns:
            Product image URL or empty string if not found
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not html_content:
            logger.warning(f"No HTML content provided for {url}")
            return ""
        
        logger.info(f"Extracting image from {url} (HTML length: {len(html_content)} chars)")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        base_domain = "/".join(url.split("/")[:3])
        
        # Amazon product image selectors
        if "amazon.com" in url:
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
                            import json
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
        
        # Home Depot product image selectors
        elif "homedepot.com" in url:
            selectors = [
                '#product-image-main img',
                '#product-image-main',
                '.product-image img',
                '.product-image',
                '[data-testid="product-image"] img',
                '[data-testid="product-image"]',
                'img.product-image',
                '.media-gallery img',
                '.media-gallery',
                '.product-hero img',
                '.product-hero',
                '.zoom img',
                '.zoom',
                'img[alt*="Home Depot"]',
                'img[alt*="generator"]',
                'img[alt*="inverter"]'
            ]
            
            for selector in selectors:
                img = soup.select_one(selector)
                if img:
                    logger.info(f"Found Home Depot image with selector: {selector}")
                    img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if img_url:
                        if img_url.startswith('//'):
                            img_url = 'https:' + img_url
                        elif img_url.startswith('/'):
                            img_url = base_domain + img_url
                        if img_url.startswith('http'):
                            logger.info(f"Extracted Home Depot image URL: {img_url}")
                            return img_url
            
            logger.warning(f"No Home Depot image found with selectors for {url}")
        
        # Walmart product image selectors
        elif "walmart.com" in url:
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
        
        # Lowes product image selectors
        elif "lowes.com" in url:
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
        
        # Fallback: look for any large image that might be a product image
        # Look for images with common product image attributes
        fallback_selectors = [
            'img[alt*="product" i]',
            'img[class*="product" i]',
            'img[class*="main" i]',
            'img[class*="hero" i]'
        ]
        
        for selector in fallback_selectors:
            imgs = soup.select(selector)
            for img in imgs:
                img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if img_url and ('product' in img_url.lower() or 'main' in img_url.lower()):
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = base_domain + img_url
                    if img_url.startswith('http') and len(img_url) > 20:  # Filter out small placeholder images
                        return img_url
        
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

