"""
Unit conversion utility for product data extraction
"""
from typing import Optional, Tuple, Dict
import re

# Common unit conversions (to base unit)
# Format: (from_unit, to_unit): conversion_factor
UNIT_CONVERSIONS: Dict[Tuple[str, str], float] = {
    # Volume
    ("gallons", "liters"): 3.78541,
    ("gal", "liters"): 3.78541,
    ("liters", "gallons"): 1 / 3.78541,
    ("L", "gallons"): 1 / 3.78541,
    ("liters", "gal"): 1 / 3.78541,
    ("L", "gal"): 1 / 3.78541,
    
    # Weight
    ("lbs", "kg"): 0.453592,
    ("pounds", "kg"): 0.453592,
    ("lb", "kg"): 0.453592,
    ("kg", "lbs"): 1 / 0.453592,
    ("kg", "pounds"): 1 / 0.453592,
    ("kg", "lb"): 1 / 0.453592,
    ("kilograms", "lbs"): 1 / 0.453592,
    ("kilograms", "pounds"): 1 / 0.453592,
    
    ("oz", "lbs"): 1 / 16.0,
    ("ounces", "lbs"): 1 / 16.0,
    ("lbs", "oz"): 16.0,
    ("pounds", "oz"): 16.0,
    
    # Length/Distance
    ("inches", "cm"): 2.54,
    ("in", "cm"): 2.54,
    ("cm", "inches"): 1 / 2.54,
    ("cm", "in"): 1 / 2.54,
    ("centimeters", "inches"): 1 / 2.54,
    
    ("feet", "meters"): 0.3048,
    ("ft", "meters"): 0.3048,
    ("meters", "feet"): 1 / 0.3048,
    ("m", "feet"): 1 / 0.3048,
    ("meters", "ft"): 1 / 0.3048,
    
    # Power
    ("kW", "W"): 1000.0,
    ("kilowatts", "W"): 1000.0,
    ("W", "kW"): 1 / 1000.0,
    ("watts", "kW"): 1 / 1000.0,
    
    # Currency (mostly for display, but included for completeness)
    ("USD", "USD"): 1.0,
    ("$", "USD"): 1.0,
    ("cents", "USD"): 1 / 100.0,
    ("USD", "cents"): 100.0,
}

# Unit aliases/normalization
UNIT_ALIASES: Dict[str, str] = {
    # Volume
    "gal": "gallons",
    "gallon": "gallons",
    "L": "liters",
    "liter": "liters",
    "litre": "liters",
    
    # Weight
    "lb": "lbs",
    "pound": "lbs",
    "pounds": "lbs",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "oz": "oz",
    "ounce": "oz",
    "ounces": "oz",
    
    # Length
    "in": "inches",
    "inch": "inches",
    "cm": "cm",
    "centimeter": "cm",
    "centimeters": "cm",
    "ft": "feet",
    "foot": "feet",
    "m": "meters",
    "meter": "meters",
    "metre": "meters",
    
    # Power
    "W": "W",
    "watt": "W",
    "watts": "W",
    "kW": "kW",
    "kilowatt": "kW",
    "kilowatts": "kW",
    
    # Currency
    "$": "USD",
    "usd": "USD",
    "dollars": "USD",
    "dollar": "USD",
}


class UnitConverter:
    """Service for converting between units"""
    
    @staticmethod
    def normalize_unit(unit: str) -> str:
        """
        Normalize unit string to standard form
        
        Args:
            unit: Unit string (e.g., "gal", "gallons", "GAL")
            
        Returns:
            Normalized unit string
        """
        if not unit:
            return ""
        
        unit_lower = unit.lower().strip()
        
        # Check aliases
        if unit_lower in UNIT_ALIASES:
            return UNIT_ALIASES[unit_lower]
        
        # Try direct match (case-insensitive)
        for alias, normalized in UNIT_ALIASES.items():
            if unit_lower == alias.lower():
                return normalized
        
        # Return original if no match (might be a valid unit we don't know)
        return unit_lower
    
    @staticmethod
    def are_units_compatible(unit1: str, unit2: str) -> bool:
        """
        Check if two units are compatible (same type)
        
        Args:
            unit1: First unit
            unit2: Second unit
            
        Returns:
            True if units are compatible
        """
        norm1 = UnitConverter.normalize_unit(unit1)
        norm2 = UnitConverter.normalize_unit(unit2)
        
        # Same unit
        if norm1 == norm2:
            return True
        
        # Check if conversion exists
        return (norm1, norm2) in UNIT_CONVERSIONS or (norm2, norm1) in UNIT_CONVERSIONS
    
    @staticmethod
    def convert(value: float, from_unit: str, to_unit: str) -> Optional[float]:
        """
        Convert a value from one unit to another
        
        Args:
            value: Numeric value to convert
            from_unit: Source unit
            to_unit: Target unit
            
        Returns:
            Converted value, or None if conversion not possible
        """
        norm_from = UnitConverter.normalize_unit(from_unit)
        norm_to = UnitConverter.normalize_unit(to_unit)
        
        # Same unit, no conversion needed
        if norm_from == norm_to:
            return value
        
        # Direct conversion
        if (norm_from, norm_to) in UNIT_CONVERSIONS:
            return value * UNIT_CONVERSIONS[(norm_from, norm_to)]
        
        # Reverse conversion
        if (norm_to, norm_from) in UNIT_CONVERSIONS:
            return value / UNIT_CONVERSIONS[(norm_to, norm_from)]
        
        # No conversion found
        return None
    
    @staticmethod
    def extract_unit_from_string(text: str) -> Optional[str]:
        """
        Extract unit from a string like "1.6 gallons" or "2000W"
        
        Args:
            text: String containing value and unit
            
        Returns:
            Extracted unit string, or None if not found
        """
        if not text or not isinstance(text, str):
            return None
        
        text = text.strip()
        
        # Remove currency symbols and common prefixes
        text = re.sub(r'^[$€£¥]', '', text)
        text = text.strip()
        
        # Pattern 1: Number followed by unit (e.g., "1.6 gallons", "2000W")
        # Match: number(s) followed by optional space and unit text
        match = re.search(r'[\d.,]+(?:\s*)([a-zA-Z]+(?:\s+[a-zA-Z]+)?)', text)
        if match:
            potential_unit = match.group(1).strip().lower()
            # Filter out common non-unit words
            non_units = {'per', 'each', 'total', 'max', 'min', 'up', 'to', 'at', 'for', 'with', 'and', 'or'}
            if potential_unit not in non_units and len(potential_unit) <= 20:  # Reasonable unit length
                return potential_unit
        
        # Pattern 2: Unit before number (less common, e.g., "USD 199.99")
        match = re.search(r'^([a-zA-Z]+)\s+[\d.,]+', text)
        if match:
            potential_unit = match.group(1).strip().lower()
            if potential_unit in ['usd', 'eur', 'gbp', 'cad']:  # Common currency prefixes
                return potential_unit
        
        return None

