"""
Alert calculator service for aggregating comparisons and calculating trends
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict


class AlertCalculatorService:
    """Service for calculating alerts and dashboard summaries"""
    
    def calculate_summary(self, comparison_results: List[Dict[str, Any]], price_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate dashboard summary from comparison results and price history
        
        Args:
            comparison_results: List of comparison results from ComparatorService
            price_history: List of price history records
            
        Returns:
            Summary dictionary with counts and percentage changes
        """
        price_drops = []
        spec_disadvantages = []
        price_increases = []
        
        # Analyze comparison results
        for result in comparison_results:
            comparison = result.get("comparison", {})
            
            # Check for price drops (red alerts)
            fields = comparison.get("fields", {})
            for field_name, field_comp in fields.items():
                if field_comp.get("alert") == "red":
                    # This is a price drop or similar disadvantage
                    if "price" in field_name.lower():
                        price_drops.append(result["listing_id"])
                    else:
                        spec_disadvantages.append(result["listing_id"])
            
            # Check for spec disadvantages (yellow alerts)
            for field_name, field_comp in fields.items():
                if field_comp.get("alert") == "yellow":
                    spec_disadvantages.append(result["listing_id"])
            
            # Check metrics
            metrics = comparison.get("metrics", {})
            for metric_name, metric_comp in metrics.items():
                if metric_comp.get("alert") == "yellow":
                    spec_disadvantages.append(result["listing_id"])
        
        # Analyze price history for trends
        # Group by listing_id
        listing_history = defaultdict(list)
        for record in price_history:
            listing_id = record.get("listing_id")
            if listing_id:
                listing_history[listing_id].append(record)
        
        # Calculate price changes
        for listing_id, history in listing_history.items():
            if len(history) < 2:
                continue
            
            # Sort by recorded_at
            history.sort(key=lambda x: x.get("recorded_at", ""))
            
            # Get first and last price
            first_record = history[0]
            last_record = history[-1]
            
            # Extract price from data JSONB
            first_data = first_record.get("data", {})
            last_data = last_record.get("data", {})
            
            # Find price field (could be "price" or similar)
            first_price = None
            last_price = None
            
            for key in ["price", "Price", "PRICE"]:
                if key in first_data:
                    first_price = first_data[key]
                if key in last_data:
                    last_price = last_data[key]
            
            if first_price and last_price:
                try:
                    first_price = float(first_price)
                    last_price = float(last_price)
                    
                    if last_price > first_price:
                        price_increases.append(listing_id)
                    elif last_price < first_price:
                        if listing_id not in price_drops:
                            price_drops.append(listing_id)
                except (ValueError, TypeError):
                    pass
        
        # Calculate percentage changes (simplified - would need more sophisticated calculation)
        price_drop_count = len(set(price_drops))
        spec_disadvantage_count = len(set(spec_disadvantages))
        price_increase_count = len(set(price_increases))
        
        total_listings = len(set(r["listing_id"] for r in comparison_results))
        
        price_drop_pct = (price_drop_count / total_listings * 100) if total_listings > 0 else 0
        spec_disadvantage_pct = (spec_disadvantage_count / total_listings * 100) if total_listings > 0 else 0
        price_increase_pct = (price_increase_count / total_listings * 100) if total_listings > 0 else 0
        
        return {
            "summary": {
                "price_drops": {
                    "count": price_drop_count,
                    "percentage_change": -price_drop_pct  # Negative for drops
                },
                "spec_disadvantages": {
                    "count": spec_disadvantage_count,
                    "percentage_change": spec_disadvantage_pct
                },
                "price_increases": {
                    "count": price_increase_count,
                    "percentage_change": price_increase_pct
                }
            },
            "listing_alerts": [
                {
                    "listing_id": listing_id,
                    "alerts": self._get_alerts_for_listing(listing_id, comparison_results),
                    "severity": self._calculate_severity(listing_id, comparison_results)
                }
                for listing_id in set(r["listing_id"] for r in comparison_results)
            ]
        }
    
    def _get_alerts_for_listing(self, listing_id: str, comparison_results: List[Dict[str, Any]]) -> List[str]:
        """Get alert types for a specific listing"""
        alerts = []
        
        for result in comparison_results:
            if result.get("listing_id") != listing_id:
                continue
            
            comparison = result.get("comparison", {})
            
            # Check fields
            for field_name, field_comp in comparison.get("fields", {}).items():
                if field_comp.get("alert") == "red":
                    alerts.append("price_drop")
                elif field_comp.get("alert") == "yellow":
                    alerts.append("spec_disadvantage")
            
            # Check metrics
            for metric_name, metric_comp in comparison.get("metrics", {}).items():
                if metric_comp.get("alert") == "yellow":
                    alerts.append("spec_disadvantage")
        
        return list(set(alerts))
    
    def _calculate_severity(self, listing_id: str, comparison_results: List[Dict[str, Any]]) -> str:
        """Calculate alert severity for a listing"""
        alerts = self._get_alerts_for_listing(listing_id, comparison_results)
        
        if "price_drop" in alerts and "spec_disadvantage" in alerts:
            return "high"
        elif "price_drop" in alerts or "spec_disadvantage" in alerts:
            return "medium"
        else:
            return "low"

