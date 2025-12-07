# Analysis Scripts

## analyze_search_pages.py

Crawls search pages from each retailer and analyzes URL patterns found in the HTML.

### Usage

```bash
cd backend
python scripts/analyze_search_pages.py
```

Or if using a virtual environment:

```bash
cd backend
source venv/bin/activate  # or your venv activation
python scripts/analyze_search_pages.py
```

### What it does

1. Crawls one search page from each retailer (Amazon, Home Depot, Walmart, Lowes)
2. Saves the raw HTML to `backend/analysis/search_pages/{retailer}_search.html`
3. Extracts all links from the page
4. Saves all links to `backend/analysis/search_pages/{retailer}_all_links.json`
5. Identifies potential product links based on URL patterns
6. Saves product links to `backend/analysis/search_pages/{retailer}_product_links.json`
7. Analyzes and displays URL patterns found

### Output

The script creates an `analysis/search_pages/` directory with:
- `{retailer}_search.html` - Raw HTML from search page
- `{retailer}_all_links.json` - All links found on the page
- `{retailer}_product_links.json` - Links that match product URL patterns

### Next Steps

After running the script:
1. Review the HTML files to understand page structure
2. Review the product_links.json files to see actual URL formats
3. Update `app/services/crawler.py` URL extraction logic based on findings

