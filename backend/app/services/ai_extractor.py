"""
AI extractor service using OpenRouter with Gemini Flash Lite for schema-guided extraction
"""
from typing import Dict, Any
from openai import AsyncOpenAI
from app.config import settings
from app.models.schema import ProductSchema, FieldDefinition


class AIExtractorService:
    """Service for extracting product data using AI"""
    
    def __init__(self):
        # Use OpenRouter with OpenAI-compatible API
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL
        )
        self.model = "google/gemini-flash-1.5"  # Gemini Flash Lite via OpenRouter
    
    def _build_extraction_prompt(self, schema: ProductSchema) -> str:
        """
        Build extraction prompt from schema
        
        Args:
            schema: Product schema definition
            
        Returns:
            Prompt string for OpenAI
        """
        field_descriptions = []
        
        for field in schema.fields:
            field_desc = f"- {field.name} ({field.type}"
            if field.unit:
                field_desc += f", unit: {field.unit}"
            field_desc += f"): {field.label}"
            field_descriptions.append(field_desc)
        
        prompt = f"""Extract the following product specifications from the provided product page content.

Fields to extract:
{chr(10).join(field_descriptions)}

Return the data as a JSON object with the exact field names as keys. Use null for fields that cannot be found.
Ensure numeric values are properly formatted (integers for integer fields, decimals for decimal fields).
Convert units to match the specified units if needed.

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
        
        # Add crawled content
        content_text = crawled_content.get("text", crawled_content.get("html", ""))
        full_prompt = prompt + content_text[:10000]  # Limit content length
        
        # Call OpenRouter (Gemini Flash Lite)
        # Note: Gemini models may not support response_format, so we'll request JSON in the prompt
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a product data extraction assistant. Extract product specifications from web pages and return them as JSON. Always return valid JSON only, no additional text."
                },
                {
                    "role": "user",
                    "content": full_prompt + "\n\nReturn only valid JSON, no markdown formatting or code blocks."
                }
            ],
            temperature=0.1,
            extra_headers={
                "HTTP-Referer": "https://competitive-edge-engine.com",  # Optional: for OpenRouter tracking
                "X-Title": "Competitive Edge Engine"
            }
        )
        
        # Parse response
        import json
        import re
        
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
        
        extracted_data = json.loads(content)
        
        # Validate and normalize
        from app.services.schema_validator import SchemaValidator
        
        # Normalize data types
        normalized_data = SchemaValidator.normalize_data(extracted_data, schema)
        
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

