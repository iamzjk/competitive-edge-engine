"""
AI extractor service using OpenRouter with Gemini 2.5 Flash Lite for schema-guided extraction
"""
import logging
from typing import Dict, Any
from openai import AsyncOpenAI
from app.config import settings
from app.models.schema import ProductSchema, FieldDefinition

logger = logging.getLogger(__name__)


class AIExtractorService:
    """Service for extracting product data using AI"""
    
    def __init__(self):
        # Validate API key is set
        if not settings.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is not set in environment variables")
        
        # Use OpenRouter with OpenAI-compatible API
        # According to OpenRouter docs: set base_url and api_key, pass optional headers in extra_headers
        self.client = AsyncOpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY
        )
        self.model = "google/gemini-2.5-flash-lite"  # Gemini 2.5 Flash Lite via OpenRouter
    
    def _build_extraction_prompt(self, schema: ProductSchema) -> str:
        """
        Build extraction prompt from schema
        
        Args:
            schema: Product schema definition
            
        Returns:
            Prompt string for OpenAI
        """
        field_descriptions = []
        
        # Check if name field exists in schema
        has_name_field = any(field.name == "name" for field in schema.fields)
        
        # Always include name field first if it exists, or add it if missing
        if has_name_field:
            # Name field exists, build descriptions normally
            for field in schema.fields:
                field_desc = f"- {field.name} ({field.type}"
                if field.unit:
                    field_desc += f", unit: {field.unit}"
                field_desc += f"): {field.label}"
                field_descriptions.append(field_desc)
        else:
            # Name field doesn't exist in schema, add it first
            field_descriptions.append("- name (text): Product name or title")
        for field in schema.fields:
            field_desc = f"- {field.name} ({field.type}"
            if field.unit:
                field_desc += f", unit: {field.unit}"
            field_desc += f"): {field.label}"
            field_descriptions.append(field_desc)
        
        prompt = f"""Extract the following product specifications from the provided product page content.

CRITICAL: You MUST extract the product name/title. Look for the main product title, heading, or product name prominently displayed on the page.

Fields to extract:
{chr(10).join(field_descriptions)}

Return the data as a JSON object with the exact field names as keys. Use null for fields that cannot be found.
Ensure numeric values are properly formatted (integers for integer fields, decimals for decimal fields).

UNIT HANDLING:
- For fields with units specified in the schema, extract BOTH the numeric value AND the unit
- Return as an object: {{"value": 1.6, "unit": "gallons"}} OR just the numeric value if unit matches schema
- If the extracted unit differs from the schema unit, include both so conversion can happen
- For fields without units in schema, return just the numeric value

IMPORTANT FOR NUMERIC FIELDS:
- Extract the numeric value as a number (not string)
- Include the unit if it differs from schema unit or if field has a unit specified
- For decimal fields: extract as decimal number (e.g., 1.6)
- For integer fields: extract as whole number (e.g., 2000)

IMPORTANT FOR PRICE FIELDS:
- Extract as decimal number (e.g., 199.99)
- Remove currency symbols ($, €, £, etc.) and commas
- Unit should be "USD" if specified in schema

EXAMPLES:
- Field with unit "gallons" in schema, page shows "1.6 gallons" → {{"value": 1.6, "unit": "gallons"}} OR just 1.6
- Field with unit "gallons" in schema, page shows "6 liters" → {{"value": 6, "unit": "liters"}}
- Field with unit "W" in schema, page shows "2000W" → {{"value": 2000, "unit": "W"}} OR just 2000
- Field without unit, page shows "$199.99" → 199.99

The "name" field is REQUIRED - always extract the product name/title as a string.

Product page content:
"""
        
        return prompt
    
    async def extract_from_content(self, crawled_content: Dict[str, Any], schema: ProductSchema) -> Dict[str, Any]:
        """
        Extract product data from crawled content using schema
        
        Args:
            crawled_content: Crawled content dictionary
            schema: Product schema to guide extraction
            
        Returns:
            Extracted data dictionary matching schema
        """
        # Build prompt
        prompt = self._build_extraction_prompt(schema)
        
        # Get content - prefer markdown/cleaned HTML, fallback to raw HTML
        content_text = crawled_content.get("text", "")
        if not content_text:
            content_text = crawled_content.get("html", "")
        
        # For Amazon pages, try to extract key product information sections
        url = crawled_content.get("url", "")
        if "amazon.com" in url and ("/dp/" in url or "/gp/product/" in url):
            # Try to extract product title and key details from HTML if available
            html_content = crawled_content.get("html", "")
            if html_content:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Extract product title
                    title_elem = soup.find(id="productTitle") or soup.find(class_="product-title")
                    if title_elem:
                        product_title = title_elem.get_text(strip=True)
                        # Prepend title to content for better context
                        content_text = f"Product Title: {product_title}\n\n" + content_text
                    
                    # Extract key product details
                    feature_bullets = soup.find(id="feature-bullets")
                    if feature_bullets:
                        features = feature_bullets.get_text(separator="\n", strip=True)
                        content_text += f"\n\nProduct Features:\n{features[:2000]}"  # Limit features length
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Error extracting Amazon-specific content: {e}")
        
        # Limit content length but ensure we have enough context
        # Increase limit for better extraction (Amazon pages can be large)
        content_limit = 15000 if "amazon.com" in url else 10000
        if len(content_text) > content_limit:
            # Try to keep the beginning (usually has product title and key info)
            # and truncate from the middle/end
            content_text = content_text[:content_limit]
        
        full_prompt = prompt + content_text
        
        # Call OpenRouter (Gemini 2.5 Flash Lite)
        # Note: Gemini models may not support response_format, so we'll request JSON in the prompt
        # Pass optional headers in extra_headers per OpenRouter documentation
        try:
            # Enhanced system prompt for better extraction
            system_prompt = """You are a product data extraction assistant. Extract product specifications from web pages and return them as JSON.

Important guidelines:
1. Always extract the product name/title - this is critical. Look for product titles, headings, or product names prominently displayed.
2. Extract all requested fields from the schema. Use null for fields that cannot be found.
3. For numeric values, extract the actual numbers and convert units if needed.
4. Return ONLY valid JSON, no markdown formatting, no code blocks, no explanations.
5. The JSON keys must match the exact field names from the schema."""
            
            user_prompt = full_prompt + "\n\nReturn ONLY valid JSON object with the exact field names as keys. No markdown, no code blocks, no explanations - just the JSON object."
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=0.1,
                extra_headers={
                    "HTTP-Referer": "https://competitive-edge-engine.com",  # Optional. Site URL for rankings on openrouter.ai
                    "X-Title": "Competitive Edge Engine"  # Optional. Site title for rankings on openrouter.ai
                }
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"OpenRouter API error: {str(e)}")
            logger.error(f"API Key present: {bool(settings.OPENROUTER_API_KEY)}")
            raise
        
        # Parse response
        import json
        import re
        import logging
        
        logger = logging.getLogger(__name__)
        
        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON if wrapped in markdown code blocks (Gemini sometimes wraps JSON)
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
        
        try:
            extracted_data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from AI response: {e}")
            logger.debug(f"AI response content: {content[:500]}")
            # Try to at least extract product name if possible before failing
            extracted_data = {field.name: None for field in schema.fields}
            # Always try to extract name, even if not in schema
            name_match = re.search(r'(?:name|title|product)[\s:]*["\']?([^"\']{5,100})["\']?', content, re.IGNORECASE)
            if name_match:
                extracted_data["name"] = name_match.group(1).strip()
            # Re-raise the exception so caller knows extraction failed
            raise ValueError(f"Failed to parse JSON from AI response: {e}. Response preview: {content[:200]}")
        
        # Ensure name field exists - extract from HTML if missing
        if "name" not in extracted_data or not extracted_data.get("name") or extracted_data.get("name", "").strip().lower() in ["null", "none", "unknown", "n/a"]:
            url = crawled_content.get("url", "")
            html_content = crawled_content.get("html", "")
            if html_content:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Try multiple selectors for product name
                    title_elem = (
                        soup.find(id="productTitle") or 
                        soup.find(class_="product-title") or
                        soup.find("h1") or
                        soup.find("h2")
                    )
                    if title_elem:
                        product_title = title_elem.get_text(strip=True)
                        if product_title and len(product_title) > 5:  # Valid title
                            extracted_data["name"] = product_title
                            logger.info(f"Extracted product name from HTML: {product_title[:50]}...")
                except Exception as e:
                    logger.debug(f"Error extracting name from HTML: {e}")
        
        # Validate and normalize
        from app.services.schema_validator import SchemaValidator
        
        # Preserve name field before normalization (in case it's not in schema)
        name_value = extracted_data.get("name")
        
        # Pre-process numeric fields: extract, validate, and convert units
        from app.services.unit_converter import UnitConverter
        import re
        
        for field in schema.fields:
            if field.name not in extracted_data:
                continue
            
            value = extracted_data[field.name]
            
            # Skip null/empty values
            if value is None or value == "null" or value == "none":
                continue
            
            # Handle different value formats from AI
            extracted_value = None
            extracted_unit = None
            
            # Case 1: Value is already a number (no unit info)
            if isinstance(value, (int, float)):
                extracted_value = float(value) if field.type == "decimal" else int(value)
                extracted_unit = field.unit  # Assume schema unit if no unit provided
            
            # Case 2: Value is an object with value and unit
            elif isinstance(value, dict) and "value" in value:
                extracted_value = value.get("value")
                extracted_unit = value.get("unit")
                if extracted_value is not None:
                    try:
                        extracted_value = float(extracted_value) if field.type == "decimal" else int(extracted_value)
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert value for {field.name}: {value}")
                        continue
            
            # Case 3: Value is a string (need to parse)
            elif isinstance(value, str):
                # Try to extract numeric value and unit from string
                # Patterns: "1.6 gallons", "2000W", "1.6gal", "$199.99"
                value_str = value.strip()
                
                # Handle price fields (remove currency symbols)
                if field.name.lower() == "price" or (field.unit and field.unit.upper() in ["USD", "CURRENCY"]):
                    try:
                        price_value = float(value_str.replace("$", "").replace(",", "").replace("€", "").replace("£", "").strip())
                        extracted_value = price_value
                        extracted_unit = field.unit or "USD"
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse price for {field.name}: {value}")
                        continue
                else:
                    # Extract numeric value
                    if field.type == "decimal":
                        number_match = re.search(r'(\d+\.?\d*)', value_str)
                    else:  # integer
                        number_match = re.search(r'(\d+)', value_str)
                    
                    if number_match:
                        try:
                            extracted_value = float(number_match.group(1)) if field.type == "decimal" else int(number_match.group(1))
                            # Try to extract unit
                            extracted_unit = UnitConverter.extract_unit_from_string(value_str) or field.unit
                        except (ValueError, TypeError):
                            logger.warning(f"Could not parse numeric value for {field.name}: {value}")
                            continue
                    else:
                        logger.warning(f"Could not find numeric value in {field.name}: {value}")
                        continue
            
            # If we have a value, handle unit conversion
            if extracted_value is not None:
                # Normalize units
                schema_unit = field.unit
                if extracted_unit:
                    extracted_unit_normalized = UnitConverter.normalize_unit(extracted_unit)
                else:
                    extracted_unit_normalized = None
                
                schema_unit_normalized = UnitConverter.normalize_unit(schema_unit) if schema_unit else None
                
                # Convert unit if needed
                if schema_unit and extracted_unit_normalized and extracted_unit_normalized != schema_unit_normalized:
                    # Check if units are compatible
                    if UnitConverter.are_units_compatible(extracted_unit_normalized, schema_unit_normalized):
                        converted_value = UnitConverter.convert(extracted_value, extracted_unit_normalized, schema_unit_normalized)
                        if converted_value is not None:
                            logger.info(f"Converted {field.name}: {extracted_value} {extracted_unit_normalized} → {converted_value} {schema_unit_normalized}")
                            extracted_value = converted_value
                        else:
                            logger.warning(f"Could not convert {field.name} from {extracted_unit_normalized} to {schema_unit_normalized}")
                    else:
                        logger.warning(f"Incompatible units for {field.name}: extracted '{extracted_unit_normalized}' vs schema '{schema_unit_normalized}'")
                
                # Ensure value is proper type before storing
                try:
                    if field.type == "decimal":
                        final_value = float(extracted_value)
                    elif field.type == "integer":
                        final_value = int(extracted_value)
                    else:
                        final_value = extracted_value
                    
                    # Store normalized value (ensure it's a number, not dict/string)
                    extracted_data[field.name] = final_value
                    logger.debug(f"Stored {field.name} = {final_value} (type: {type(final_value).__name__})")
                except (ValueError, TypeError) as e:
                    logger.error(f"Could not convert {field.name} value {extracted_value} to {field.type}: {e}")
                    # Remove invalid value so validation can catch it
                    if field.name in extracted_data:
                        del extracted_data[field.name]
            else:
                # If we couldn't extract a value, remove the field entry if it's invalid
                if field.name in extracted_data and isinstance(extracted_data[field.name], dict):
                    # Remove dict values that weren't processed
                    logger.warning(f"Removing unprocessed dict value for {field.name}: {extracted_data[field.name]}")
                    del extracted_data[field.name]
        
        # Final cleanup: ensure all numeric fields are proper types (not dicts or strings)
        for field in schema.fields:
            if field.name in extracted_data:
                value = extracted_data[field.name]
                # If value is still a dict (shouldn't happen, but safety check)
                if isinstance(value, dict):
                    if "value" in value:
                        try:
                            extracted_data[field.name] = float(value["value"]) if field.type == "decimal" else int(value["value"])
                            logger.warning(f"Cleaned up dict value for {field.name}")
                        except (ValueError, TypeError):
                            logger.error(f"Could not extract value from dict for {field.name}: {value}")
                            extracted_data[field.name] = None
                    else:
                        logger.error(f"Dict value for {field.name} missing 'value' key: {value}")
                        extracted_data[field.name] = None
                # If value is a string for numeric field (shouldn't happen after preprocessing, but safety check)
                elif isinstance(value, str) and field.type in ["integer", "decimal"]:
                    try:
                        # Try to extract number from string
                        import re
                        if field.type == "decimal":
                            number_match = re.search(r'(\d+\.?\d*)', value)
                        else:
                            number_match = re.search(r'(\d+)', value)
                        if number_match:
                            extracted_data[field.name] = float(number_match.group(1)) if field.type == "decimal" else int(number_match.group(1))
                            logger.warning(f"Cleaned up string value for {field.name}: '{value}' → {extracted_data[field.name]}")
                        else:
                            logger.error(f"Could not extract number from string for {field.name}: '{value}'")
                            extracted_data[field.name] = None
                    except (ValueError, TypeError):
                        logger.error(f"Could not parse string value for {field.name}: '{value}'")
                        extracted_data[field.name] = None
        
        # Normalize data types (this will skip fields not in schema)
        normalized_data = SchemaValidator.normalize_data(extracted_data, schema)
        
        # Always include name field even if not in schema (required for product matching)
        if name_value and name_value not in ["null", "none", "unknown", "n/a", None]:
            normalized_data["name"] = str(name_value).strip()
        elif not normalized_data.get("name"):
            # If still no name, try one more time from HTML
            html_content = crawled_content.get("html", "")
            if html_content:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    title_elem = soup.find(id="productTitle") or soup.find(class_="product-title") or soup.find("h1")
                    if title_elem:
                        product_title = title_elem.get_text(strip=True)
                        if product_title and len(product_title) > 5:
                            normalized_data["name"] = product_title
                except Exception:
                    pass
        
        return normalized_data
    
    async def extract_from_url(self, url: str, schema: ProductSchema) -> Dict[str, Any]:
        """
        Extract product data directly from URL
        
        Args:
            url: Product URL
            schema: Product schema
            
        Returns:
            Extracted data dictionary
        """
        from app.services.crawler import CrawlerService
        
        crawler = CrawlerService()
        crawled_content = await crawler.crawl_url(url)
        
        return await self.extract_from_content(crawled_content, schema)

