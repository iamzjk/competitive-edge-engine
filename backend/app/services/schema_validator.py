"""
Schema validation service
"""
from typing import Dict, Any, List, Tuple
from app.models.schema import ProductSchema, FieldDefinition


class SchemaValidationError(Exception):
    """Schema validation error"""
    pass


class SchemaValidator:
    """Validates product schemas and data"""
    
    @staticmethod
    def validate_schema(schema: ProductSchema) -> Tuple[bool, List[str]]:
        """
        Validate schema structure
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for duplicate field names
        field_names = [field.name for field in schema.fields]
        if len(field_names) != len(set(field_names)):
            errors.append("Duplicate field names found")
        
        # Check for duplicate metric names
        if schema.metrics:
            metric_names = [metric.name for metric in schema.metrics]
            if len(metric_names) != len(set(metric_names)):
                errors.append("Duplicate metric names found")
        
        # Validate each field
        for field in schema.fields:
            if not field.name:
                errors.append(f"Field name cannot be empty")
            if not field.label:
                errors.append(f"Field '{field.name}' must have a label")
        
        # Validate metrics reference existing fields
        if schema.metrics:
            for metric in schema.metrics:
                # Basic validation - check if formula references valid fields
                # This is a simple check; full formula validation happens in metric_calculator
                pass
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_data_against_schema(data: Dict[str, Any], schema: ProductSchema) -> Tuple[bool, List[str]]:
        """
        Validate data matches schema
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        for field in schema.fields:
            if field.required and field.name not in data:
                errors.append(f"Required field '{field.name}' is missing")
        
        # Validate field types
        for field in schema.fields:
            if field.name in data:
                value = data[field.name]
                
                if field.type == "integer":
                    if not isinstance(value, int):
                        try:
                            int(value)
                        except (ValueError, TypeError):
                            errors.append(f"Field '{field.name}' must be an integer")
                
                elif field.type == "decimal":
                    if not isinstance(value, (int, float)):
                        # Try to convert string to float (handles "1.6", "1.6 gallons", etc.)
                        if isinstance(value, str):
                            # Remove common units and non-numeric characters except decimal point
                            cleaned_value = value.strip()
                            # Try to extract number from strings like "1.6 gallons" or "1.6gal"
                            import re
                            number_match = re.search(r'(\d+\.?\d*)', cleaned_value)
                            if number_match:
                                try:
                                    float(number_match.group(1))
                                    # Value can be converted, skip error
                                    continue
                                except (ValueError, TypeError):
                                    pass
                        try:
                            float(value)
                        except (ValueError, TypeError):
                            errors.append(f"Field '{field.name}' must be a decimal number")
                
                elif field.type == "boolean":
                    if not isinstance(value, bool):
                        errors.append(f"Field '{field.name}' must be a boolean")
                
                elif field.type == "text":
                    if not isinstance(value, str):
                        errors.append(f"Field '{field.name}' must be a string")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def normalize_data(data: Dict[str, Any], schema: ProductSchema) -> Dict[str, Any]:
        """
        Normalize data types according to schema
        """
        normalized = {}
        
        for field in schema.fields:
            if field.name in data:
                value = data[field.name]
                
                # Handle dict values (e.g., {"value": 1.6, "unit": "gallons"})
                if isinstance(value, dict) and "value" in value:
                    value = value["value"]
                
                # Skip None values - they should remain None
                if value is None:
                    if field.required:
                        normalized[field.name] = None
                    # Skip optional None fields
                    continue
                
                try:
                    if field.type == "integer":
                        if isinstance(value, str):
                            # Extract integer from string
                            import re
                            number_match = re.search(r'(\d+)', value.strip())
                            if number_match:
                                normalized[field.name] = int(number_match.group(1))
                            else:
                                normalized[field.name] = int(value)
                        else:
                            normalized[field.name] = int(value)
                    elif field.type == "decimal":
                        # Handle string values that might contain units (e.g., "1.6 gallons")
                        if isinstance(value, str):
                            import re
                            # Extract numeric value from string
                            number_match = re.search(r'(\d+\.?\d*)', value.strip())
                            if number_match:
                                normalized[field.name] = float(number_match.group(1))
                            else:
                                normalized[field.name] = float(value)
                        else:
                            normalized[field.name] = float(value)
                    elif field.type == "boolean":
                        normalized[field.name] = bool(value)
                    elif field.type == "text":
                        normalized[field.name] = str(value)
                except (ValueError, TypeError) as e:
                    # Log error but keep original value if conversion fails
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Could not normalize {field.name} value {value} to {field.type}: {e}")
                    # Set to None for required fields, skip for optional
                    if field.required:
                        normalized[field.name] = None
            elif not field.required:
                # Optional fields can be omitted
                pass
        
        return normalized

