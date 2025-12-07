"""
Script to crawl search pages from each retailer and analyze URL patterns

Usage:
    cd backend
    python -m scripts.analyze_search_pages
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from bs4 import BeautifulSoup
from app.services.crawler import CrawlerService

# Create output directory
OUTPUT_DIR = Path(__file__).parent.parent / "analysis" / "search_pages"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

async def analyze_retailer_search(retailer: str, query: str = "2000w inverter generator"):
    """Crawl a search page and analyze URLs found"""
    print(f"\n{'='*60}")
    print(f"Analyzing {retailer.upper()}")
    print(f"{'='*60}")
    
    crawler = CrawlerService()
    
    # Build search URL
    search_urls = {
        "amazon": f"https://www.amazon.com/s?k={query.replace(' ', '+')}",
        "homedepot": f"https://www.homedepot.com/s/{query.replace(' ', '%20')}",
        "walmart": f"https://www.walmart.com/search?q={query.replace(' ', '+')}",
        "lowes": f"https://www.lowes.com/search?searchTerm={query.replace(' ', '+')}"
    }
    
    if retailer.lower() not in search_urls:
        print(f"Unknown retailer: {retailer}")
        return
    
    search_url = search_urls[retailer.lower()]
    print(f"Search URL: {search_url}")
    
    # Crawl the page
    print("Crawling...")
    content = await crawler.crawl_url(search_url, wait_for_content=True)
    
    if not content.get("success"):
        print(f"❌ Failed to crawl {retailer}")
        return
    
    html_content = content.get("html", "")
    if not html_content:
        print(f"❌ No HTML content received")
        return
    
    # Save raw HTML
    html_file = OUTPUT_DIR / f"{retailer}_search.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Saved HTML to: {html_file}")
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract ALL links
    all_links = []
    for link in soup.find_all('a', href=True):
        href = link.get('href', '').strip()
        if href:
            all_links.append({
                'href': href,
                'text': link.get_text(strip=True)[:100],  # First 100 chars of text
                'class': link.get('class', []),
                'id': link.get('id', '')
            })
    
    # Save all links
    links_file = OUTPUT_DIR / f"{retailer}_all_links.json"
    with open(links_file, 'w', encoding='utf-8') as f:
        json.dump(all_links, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved all links ({len(all_links)} total) to: {links_file}")
    
    # Analyze product URL patterns
    print(f"\n📊 Analyzing product URL patterns...")
    
    # Look for common product URL indicators
    product_patterns = {
        'amazon': ['/dp/', '/gp/product/'],
        'homedepot': ['/p/'],
        'walmart': ['/ip/'],
        'lowes': ['/pd/', '/p/']
    }
    
    patterns = product_patterns.get(retailer.lower(), [])
    product_links = []
    
    for link in all_links:
        href = link['href']
        for pattern in patterns:
            if pattern in href:
                product_links.append(link)
                break
    
    print(f"Found {len(product_links)} potential product links")
    
    # Analyze patterns
    if product_links:
        print(f"\n🔍 Sample product URLs:")
        for i, link in enumerate(product_links[:10], 1):
            print(f"  {i}. {link['href']}")
            if link['text']:
                print(f"     Text: {link['text'][:60]}")
            if link['class']:
                print(f"     Classes: {link['class']}")
        
        # Save product links
        products_file = OUTPUT_DIR / f"{retailer}_product_links.json"
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump(product_links, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Saved {len(product_links)} product links to: {products_file}")
        
        # Extract unique URL patterns
        print(f"\n📋 URL Pattern Analysis:")
        url_patterns = {}
        for link in product_links:
            href = link['href']
            # Try to identify the pattern
            if href.startswith('http'):
                domain = href.split('/')[2]
                path = '/' + '/'.join(href.split('/')[3:]).split('?')[0].split('#')[0]
            elif href.startswith('/'):
                path = href.split('?')[0].split('#')[0]
            else:
                continue
            
            # Extract pattern (e.g., /dp/B0DH9ZJHN9, /p/Product-Name/123456)
            pattern_key = path[:50]  # First 50 chars to see pattern
            if pattern_key not in url_patterns:
                url_patterns[pattern_key] = []
            url_patterns[pattern_key].append(href)
        
        print(f"\nUnique URL patterns found:")
        for pattern, urls in list(url_patterns.items())[:5]:
            print(f"  Pattern: {pattern}")
            print(f"  Count: {len(urls)}")
            print(f"  Example: {urls[0]}")
            if len(urls) > 1:
                print(f"  Another: {urls[1] if len(urls) > 1 else ''}")
            print()
    else:
        print(f"⚠️  No product links found with patterns: {patterns}")
        print(f"   This might indicate:")
        print(f"   - The page uses JavaScript to load products")
        print(f"   - Different URL structure than expected")
        print(f"   - Products are loaded via API calls")

async def main():
    """Crawl and analyze all retailers"""
    retailers = ["amazon", "homedepot", "walmart", "lowes"]
    query = "2000w inverter generator"
    
    print("="*60)
    print("RETAILER SEARCH PAGE ANALYSIS")
    print("="*60)
    print(f"Query: {query}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    for retailer in retailers:
        try:
            await analyze_retailer_search(retailer, query)
        except Exception as e:
            print(f"❌ Error analyzing {retailer}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"\nAll files saved to: {OUTPUT_DIR}")
    print("\nNext steps:")
    print("1. Review the HTML files to see the page structure")
    print("2. Review the product_links.json files to see URL patterns")
    print("3. Update crawler.py URL extraction logic based on findings")

if __name__ == "__main__":
    asyncio.run(main())

