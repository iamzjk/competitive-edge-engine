"""
One-off script to fix price fields in custom templates and products from integer to decimal

Usage:
    cd backend
    python -m scripts.fix_price_to_decimal
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_supabase

def fix_price_fields():
    """Fix price fields from integer to decimal in custom templates and products"""
    supabase = get_supabase()
    
    print("Fixing price fields in custom templates...")
    
    # Get all custom templates
    templates_response = supabase.table("product_templates").select("*").eq("is_system", False).execute()
    
    templates_updated = 0
    for template in templates_response.data:
        schema = template["schema"]
        fields = schema.get("fields", [])
        updated = False
        
        for field in fields:
            if (field.get("name", "").lower() == "price" or "price" in field.get("name", "").lower()):
                if field.get("type") == "integer":
                    field["type"] = "decimal"
                    updated = True
                    print(f"  - Updated template '{template['name']}': price field changed to decimal")
        
        if updated:
            supabase.table("product_templates").update({
                "schema": schema
            }).eq("id", template["id"]).execute()
            templates_updated += 1
    
    print(f"\nFixed {templates_updated} custom template(s)")
    
    print("\nFixing price fields in products...")
    
    # Get all products
    products_response = supabase.table("my_products").select("*").execute()
    
    products_updated = 0
    for product in products_response.data:
        schema = product["schema"]
        fields = schema.get("fields", [])
        updated = False
        
        for field in fields:
            if (field.get("name", "").lower() == "price" or "price" in field.get("name", "").lower()):
                if field.get("type") == "integer":
                    field["type"] = "decimal"
                    updated = True
                    print(f"  - Updated product '{product['name']}': price field changed to decimal")
        
        if updated:
            supabase.table("my_products").update({
                "schema": schema
            }).eq("id", product["id"]).execute()
            products_updated += 1
    
    print(f"\nFixed {products_updated} product(s)")
    print("\nDone!")

if __name__ == "__main__":
    fix_price_fields()

