"""
Schema definition models for product fields and metrics
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional, List


class FieldDefinition(BaseModel):
    """Definition of a product field"""
    name: str = Field(..., description="Field name (used as key in data JSON)")
    type: Literal["text", "integer", "decimal", "boolean"] = Field(..., description="Field data type")
    unit: Optional[str] = Field(None, description="Unit of measurement (e.g., 'USD', 'W', 'lbs')")
    label: str = Field(..., description="Display label for the field")
    compareDirection: Literal["lower", "higher"] = Field(..., description="Direction for comparison (lower/higher is better)")
    required: bool = Field(True, description="Whether field is required")


class MetricDefinition(BaseModel):
    """Definition of a calculated metric"""
    name: str = Field(..., description="Metric name")
    formula: str = Field(..., description="Formula expression (e.g., 'price / wattage')")
    label: str = Field(..., description="Display label for the metric")
    compareDirection: Literal["lower", "higher"] = Field(..., description="Direction for comparison")
    format: Optional[str] = Field(None, description="Format type (e.g., 'currency', 'percentage')")


class ProductSchema(BaseModel):
    """Product schema definition"""
    fields: List[FieldDefinition] = Field(..., description="List of field definitions")
    metrics: Optional[List[MetricDefinition]] = Field(default_factory=list, description="List of metric definitions")

