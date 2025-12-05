"""
Crawling endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.database import get_supabase
from app.services.crawler import CrawlerService
from app.services.ai_extractor import AIExtractorService

router = APIRouter(prefix="/crawl", tags=["crawl"])


class CrawlSingleRequest(BaseModel):
    """Request to crawl a single URL"""
    product_id: UUID
    url: str
    retailer_name: str


@router.post("/single")
async def crawl_single(
    request: CrawlSingleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Crawl a single URL and extract product data using product schema
    """
    supabase = get_supabase()
    
    # Get product and schema
    product_response = supabase.table("my_products").select("*").eq("id", str(request.product_id)).eq("user_id", current_user["user_id"]).execute()
    
    if not product_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product = product_response.data[0]
    
    # Crawl URL
    crawler = CrawlerService()
    crawled_content = await crawler.crawl_url(request.url)
    
    # Extract data using schema
    from app.models.schema import ProductSchema
    schema = ProductSchema(**product["schema"])
    
    extractor = AIExtractorService()
    extracted_data = await extractor.extract_from_content(crawled_content, schema)
    
    return {
        "url": request.url,
        "extracted_data": extracted_data
    }


@router.post("/batch")
async def crawl_batch(current_user: dict = Depends(get_current_user)):
    """
    Batch crawl all competitor listings for the current user
    """
    supabase = get_supabase()
    
    # Get all competitor listings
    listings_response = supabase.table("competitor_listings").select("*").eq("user_id", current_user["user_id"]).execute()
    
    if not listings_response.data:
        return {"message": "No listings to crawl", "crawled": 0}
    
    crawler = CrawlerService()
    extractor = AIExtractorService()
    
    crawled_count = 0
    errors = []
    
    for listing in listings_response.data:
        try:
            # Get product schema
            product_response = supabase.table("my_products").select("schema").eq("id", listing["my_product_id"]).execute()
            
            if not product_response.data:
                errors.append(f"Product not found for listing {listing['id']}")
                continue
            
            schema = product_response.data[0]["schema"]
            from app.models.schema import ProductSchema
            schema_obj = ProductSchema(**schema)
            
            # Crawl
            crawled_content = await crawler.crawl_url(listing["url"])
            
            # Extract
            extracted_data = await extractor.extract_from_content(crawled_content, schema_obj)
            
            # Update listing
            supabase.table("competitor_listings").update({
                "data": extracted_data,
                "last_crawled_at": "now()"
            }).eq("id", listing["id"]).execute()
            
            # Save to price history
            supabase.table("price_history").insert({
                "listing_id": listing["id"],
                "data": extracted_data
            }).execute()
            
            crawled_count += 1
            
        except Exception as e:
            errors.append(f"Error crawling {listing['url']}: {str(e)}")
    
    return {
        "message": f"Crawled {crawled_count} listings",
        "crawled": crawled_count,
        "errors": errors
    }

