"""
Comparator service for field-by-field comparison
"""
from typing import Dict, Any
from app.models.schema import ProductSchema, FieldDefinition, MetricDefinition
from app.services.metric_calculator import MetricCalculator


class ComparatorService:
    """Service for comparing products field-by-field"""
    
    def compare(self, user_data: Dict[str, Any], competitor_data: Dict[str, Any], schema: ProductSchema) -> Dict[str, Any]:
        """
        Compare user product data with competitor data
        
        Args:
            user_data: User product data
            competitor_data: Competitor product data
            schema: Product schema
            
        Returns:
            Comparison result dictionary
        """
        comparison = {
            "fields": {},
            "metrics": {}
        }
        
        # Compare fields
        for field in schema.fields:
            field_name = field.name
            
            user_value = user_data.get(field_name)
            competitor_value = competitor_data.get(field_name)
            
            if user_value is None or competitor_value is None:
                # Skip if either value is missing
                continue
            
            # Calculate difference
            if field.type in ["integer", "decimal"]:
                try:
                    user_num = float(user_value)
                    competitor_num = float(competitor_value)
                    difference = competitor_num - user_num
                    
                    # Determine advantage
                    if field.compareDirection == "lower":
                        # Lower is better
                        if competitor_num < user_num:
                            advantage = "competitor"
                            alert = "red"
                        elif competitor_num > user_num:
                            advantage = "user"
                            alert = None
                        else:
                            advantage = "equal"
                            alert = None
                    else:  # higher is better
                        # Higher is better
                        if competitor_num > user_num:
                            advantage = "competitor"
                            alert = "yellow"  # Spec disadvantage for user
                        elif competitor_num < user_num:
                            advantage = "user"
                            alert = None
                        else:
                            advantage = "equal"
                            alert = None
                    
                    comparison["fields"][field_name] = {
                        "user": user_value,
                        "competitor": competitor_value,
                        "difference": difference,
                        "advantage": advantage,
                        "alert": alert
                    }
                except (ValueError, TypeError):
                    # Non-numeric comparison
                    comparison["fields"][field_name] = {
                        "user": user_value,
                        "competitor": competitor_value,
                        "difference": None,
                        "advantage": "equal",
                        "alert": None
                    }
            else:
                # Text/boolean comparison
                comparison["fields"][field_name] = {
                    "user": user_value,
                    "competitor": competitor_value,
                    "difference": None,
                    "advantage": "equal" if user_value == competitor_value else "different",
                    "alert": None
                }
        
        # Calculate and compare metrics
        if schema.metrics:
            for metric in schema.metrics:
                try:
                    user_metric_value = MetricCalculator.calculate_metric(metric, user_data)
                    competitor_metric_value = MetricCalculator.calculate_metric(metric, competitor_data)
                    
                    difference = competitor_metric_value - user_metric_value
                    
                    # Determine advantage
                    if metric.compareDirection == "lower":
                        if competitor_metric_value < user_metric_value:
                            advantage = "competitor"
                            alert = "yellow"
                        elif competitor_metric_value > user_metric_value:
                            advantage = "user"
                            alert = None
                        else:
                            advantage = "equal"
                            alert = None
                    else:  # higher is better
                        if competitor_metric_value > user_metric_value:
                            advantage = "competitor"
                            alert = "yellow"
                        elif competitor_metric_value < user_metric_value:
                            advantage = "user"
                            alert = None
                        else:
                            advantage = "equal"
                            alert = None
                    
                    comparison["metrics"][metric.name] = {
                        "user": user_metric_value,
                        "competitor": competitor_metric_value,
                        "difference": difference,
                        "advantage": advantage,
                        "alert": alert
                    }
                except Exception as e:
                    # Skip metric if calculation fails
                    pass
        
        return comparison

