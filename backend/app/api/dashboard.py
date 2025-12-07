"""
Dashboard endpoints
"""
from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from app.middleware.auth import get_current_user
from app.database import get_supabase
from app.services.comparator import ComparatorService
from app.services.alert_calculator import AlertCalculatorService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(current_user: dict = Depends(get_current_user)):
    """
    Get dashboard summary cards data (price drops, spec disadvantages, price increases)
    """
    supabase = get_supabase()
    
    # Get all products and their competitor listings
    products_response = supabase.table("my_products").select("*").eq("user_id", current_user["user_id"]).execute()
    
    if not products_response.data:
        return {
            "summary": {
                "price_drops": {"count": 0, "percentage_change": 0},
                "spec_disadvantages": {"count": 0, "percentage_change": 0},
                "price_increases": {"count": 0, "percentage_change": 0}
            }
        }
    
    # Get all competitor listings
    listings_response = supabase.table("competitor_listings").select("*").eq("user_id", current_user["user_id"]).execute()
    
    comparator = ComparatorService()
    alert_calculator = AlertCalculatorService()
    
    # Build comparison results
    comparison_results = []
    
    for listing in listings_response.data:
        # Get product
        product = next((p for p in products_response.data if p["id"] == listing["my_product_id"]), None)
        if not product:
            continue
        
        # Compare
        from app.models.schema import ProductSchema
        schema = ProductSchema(**product["schema"])
        comparison = comparator.compare(product["data"], listing["data"], schema)
        comparison_results.append({
            "listing_id": listing["id"],
            "comparison": comparison
        })
    
    # Get price history for trends
    price_history_response = supabase.table("price_history").select("*").in_(
        "listing_id", [l["id"] for l in listings_response.data]
    ).order("recorded_at", desc=True).execute()
    
    # Calculate alerts
    summary = alert_calculator.calculate_summary(comparison_results, price_history_response.data)
    
    return summary


@router.get("/listings")
async def get_dashboard_listings(current_user: dict = Depends(get_current_user)):
    """
    Get all competitor listings with computed comparisons
    """
    supabase = get_supabase()
    
    # Get all products
    products_response = supabase.table("my_products").select("*").eq("user_id", current_user["user_id"]).execute()
    
    # Get all competitor listings
    listings_response = supabase.table("competitor_listings").select("*").eq("user_id", current_user["user_id"]).execute()
    
    comparator = ComparatorService()
    
    listings_with_comparison = []
    
    for listing in listings_response.data:
        # Get product
        product = next((p for p in products_response.data if p["id"] == listing["my_product_id"]), None)
        if not product:
            continue
        
        # Compare
        from app.models.schema import ProductSchema
        schema = ProductSchema(**product["schema"])
        comparison = comparator.compare(product["data"], listing["data"], schema)
        
        listings_with_comparison.append({
            **listing,
            "comparison": comparison,
            "product_schema": product["schema"],  # Include schema for frontend unit display
            "my_product": {  # Include user's product info for display
                "id": product["id"],
                "name": product["name"],
                "image_url": product.get("image_url") or product.get("data", {}).get("image_url") or product.get("data", {}).get("image")
            }
        })
    
    return listings_with_comparison


@router.get("/debug-images")
async def debug_images(current_user: dict = Depends(get_current_user)):
    """
    Debug endpoint to check image URLs in database
    """
    supabase = get_supabase()

    # Get all competitor listings
    listings_response = supabase.table("competitor_listings").select("id, url, image_url, product_name").eq("user_id", current_user["user_id"]).execute()

    return {
        "listings": listings_response.data,
        "total": len(listings_response.data) if listings_response.data else 0,
        "with_images": len([l for l in (listings_response.data or []) if l.get("image_url")])
    }


@router.get("/test-extract/{listing_id}")
async def test_image_extract(listing_id: str, current_user: dict = Depends(get_current_user)):
    """
    Test image extraction on a specific listing
    """
    import logging
    logger = logging.getLogger(__name__)

    supabase = get_supabase()

    # Get the listing
    listing_response = supabase.table("competitor_listings").select("*").eq("id", listing_id).eq("user_id", current_user["user_id"]).execute()

    if not listing_response.data:
        return {"error": "Listing not found"}

    listing = listing_response.data[0]

    # Crawl and extract image
    from app.services.crawler import CrawlerService
    crawler = CrawlerService()

    try:
        logger.info(f"Testing image extraction for: {listing['url']}")
        crawled_content = await crawler.crawl_url(listing["url"])
        html_content = crawled_content.get("html", "")
        image_url = crawler.extract_product_image(html_content, listing["url"]) if html_content else None

        return {
            "listing_id": listing_id,
            "url": listing["url"],
            "extracted_image_url": image_url,
            "html_length": len(html_content) if html_content else 0
        }
    except Exception as e:
        return {
            "listing_id": listing_id,
            "url": listing["url"],
            "error": str(e)
        }

