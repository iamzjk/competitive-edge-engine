"""
Image proxy endpoints to bypass CORS and referrer restrictions
"""
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import logging
from urllib.parse import urlparse, unquote

router = APIRouter(prefix="/images", tags=["images"])
logger = logging.getLogger(__name__)


class ProxyImageRequest(BaseModel):
    url: str


@router.get("/proxy")
async def proxy_image(request: Request, url: str = Query(..., description="Image URL to proxy")):
    """
    Proxy image requests to bypass CORS/referrer restrictions.
    Fetches the image server-side and serves it through our API.
    """
    # Log the raw query string for debugging
    raw_query = str(request.url.query)
    logger.info(f"Raw query string: {raw_query[:300]}")
    
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    # Log the URL as received from FastAPI
    logger.info(f"URL from FastAPI Query param: {url[:200]}")
    
    # FastAPI automatically decodes query parameters, but handle edge cases
    # The + character might be converted to space by FastAPI, so we need to handle that
    # Check if URL contains spaces that should be +
    if ' ' in url and 'amazon.com' in url:
        # Replace spaces with + for Amazon URLs (they use + in image paths)
        url = url.replace(' ', '+')
        logger.info(f"Replaced spaces with + in URL: {url[:200]}")
    
    # If URL still contains encoded characters, decode it
    try:
        if '%' in url:
            url = unquote(url, encoding='utf-8')
            logger.info(f"Decoded URL: {url[:200]}")
    except Exception as e:
        logger.warning(f"Error decoding URL: {e}, using as-is")
    
    # Validate URL - be more lenient with validation
    try:
        parsed = urlparse(url)
        logger.info(f"Parsed URL - scheme: '{parsed.scheme}', netloc: '{parsed.netloc}', path: '{parsed.path[:100]}'")
        
        # Check if scheme and netloc exist
        if not parsed.scheme:
            logger.error(f"Missing scheme in URL: {url[:200]}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid URL: missing scheme. URL: {url[:100]}"
            )
        
        if not parsed.netloc:
            logger.error(f"Missing netloc in URL: {url[:200]}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid URL: missing domain. URL: {url[:100]}"
            )
        
        # Only allow http/https
        if parsed.scheme not in ['http', 'https']:
            raise HTTPException(
                status_code=400, 
                detail=f"Only http and https URLs are allowed, got: {parsed.scheme}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing URL {url[:200]}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid URL format: {str(e)}")
    
    try:
        # Extract base domain for referer header
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Fix Amazon URLs without file extensions
        # Amazon requires .jpg extension but the crawler may have stripped it
        if 'amazon.com' in url and '/images/I/' in url:
            # Check if URL ends with an extension
            if not any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                # Add .jpg extension (Amazon's default)
                url = url + '.jpg'
                logger.info(f"Added .jpg extension to Amazon URL: {url[:200]}")
        
        logger.info(f"Fetching image from: {url[:200]}")
        
        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
            max_redirects=5
        ) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": base_url + "/",
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                }
            )
            response.raise_for_status()
            
            # Determine content type
            content_type = response.headers.get("content-type", "image/jpeg")
            
            # Validate it's actually an image
            if not content_type.startswith("image/"):
                logger.warning(f"Non-image content type received: {content_type} for URL: {url}")
                # Still return it, but log the warning
            
            return StreamingResponse(
                iter([response.content]),
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                }
            )
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching image: {url}")
        raise HTTPException(status_code=504, detail="Image request timed out")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching image: {url}, status: {e.response.status_code}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch image: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error proxying image {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to proxy image: {str(e)}")

