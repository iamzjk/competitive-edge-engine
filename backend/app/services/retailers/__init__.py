"""
Retailer registry and factory
"""
from typing import Optional
from .base import BaseRetailer
from .amazon import AmazonRetailer
from .walmart import WalmartRetailer
from .homedepot import HomeDepotRetailer
from .lowes import LowesRetailer

_RETAILER_REGISTRY = {
    "amazon": AmazonRetailer(),
    "walmart": WalmartRetailer(),
    "homedepot": HomeDepotRetailer(),
    "lowes": LowesRetailer(),
}


def get_retailer_handler(retailer_name_or_url: str) -> Optional[BaseRetailer]:
    """
    Get retailer handler by name or URL
    
    Args:
        retailer_name_or_url: Retailer name (amazon, walmart, etc.) or URL
    
    Returns:
        Retailer handler instance or None
    """
    # If URL, extract domain
    if "://" in retailer_name_or_url:
        url = retailer_name_or_url.lower()
        if "amazon.com" in url:
            return _RETAILER_REGISTRY["amazon"]
        elif "walmart.com" in url:
            return _RETAILER_REGISTRY["walmart"]
        elif "homedepot.com" in url:
            return _RETAILER_REGISTRY["homedepot"]
        elif "lowes.com" in url:
            return _RETAILER_REGISTRY["lowes"]
        return None
    
    # If name, lookup in registry
    return _RETAILER_REGISTRY.get(retailer_name_or_url.lower())


__all__ = [
    "BaseRetailer",
    "AmazonRetailer",
    "WalmartRetailer",
    "HomeDepotRetailer",
    "LowesRetailer",
    "get_retailer_handler",
]

