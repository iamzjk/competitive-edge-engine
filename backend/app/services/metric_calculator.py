"""
Metric calculator service for evaluating custom metric formulas
"""
from typing import Dict, Any
from app.models.schema import MetricDefinition
import re


class MetricCalculator:
    """Service for calculating custom metrics"""
    
    @staticmethod
    def evaluate_formula(formula: str, data: Dict[str, Any]) -> float:
        """
        Safely evaluate a metric formula with field references
        
        Args:
            formula: Formula string (e.g., "price / wattage")
            data: Data dictionary with field values
            
        Returns:
            Calculated metric value
        """
        # Replace field references with values
        # Find all field names in formula
        field_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        fields_in_formula = re.findall(field_pattern, formula)
        
        # Replace field names with their values
        safe_formula = formula
        for field_name in fields_in_formula:
            if field_name in data:
                value = data[field_name]
                # Ensure numeric value
                if isinstance(value, (int, float)):
                    safe_formula = safe_formula.replace(field_name, str(value))
                else:
                    # Try to convert
                    try:
                        numeric_value = float(value)
                        safe_formula = safe_formula.replace(field_name, str(numeric_value))
                    except (ValueError, TypeError):
                        raise ValueError(f"Cannot use non-numeric field '{field_name}' in formula")
        
        # Evaluate formula safely
        try:
            # Only allow safe operations
            allowed_chars = set('0123456789+-*/.() ')
            if not all(c in allowed_chars for c in safe_formula):
                raise ValueError("Formula contains invalid characters")
            
            result = eval(safe_formula)
            return float(result)
        except Exception as e:
            raise ValueError(f"Error evaluating formula '{formula}': {str(e)}")
    
    @staticmethod
    def calculate_metric(metric: MetricDefinition, data: Dict[str, Any]) -> float:
        """
        Calculate a metric value
        
        Args:
            metric: Metric definition
            data: Data dictionary
            
        Returns:
            Calculated metric value
        """
        return MetricCalculator.evaluate_formula(metric.formula, data)
    
    @staticmethod
    def format_metric_value(value: float, format_type: str = None) -> str:
        """
        Format metric value for display
        
        Args:
            value: Metric value
            format_type: Format type (currency, percentage, etc.)
            
        Returns:
            Formatted string
        """
        if format_type == "currency":
            return f"${value:.2f}"
        elif format_type == "percentage":
            return f"{value:.2f}%"
        else:
            return str(value)

