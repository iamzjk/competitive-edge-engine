"""
Matcher service for calculating confidence scores
"""
from typing import Dict, Any, List
from openai import AsyncOpenAI
from app.config import settings
from app.models.schema import ProductSchema


class MatcherService:
    """Service for matching products and calculating confidence scores"""
    
    def __init__(self):
        # Use OpenRouter for all AI operations (Gemini Flash Lite + OpenAI embeddings)
        self.openrouter_client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL
        )
        # Embedding model via OpenRouter
        self.embedding_model = "openai/text-embedding-3-small"
    
    def _calculate_spec_similarity(self, user_data: Dict[str, Any], candidate_data: Dict[str, Any], schema: ProductSchema) -> float:
        """
        Calculate specification similarity (60% weight)
        
        Args:
            user_data: User product data
            candidate_data: Candidate product data
            schema: Product schema
            
        Returns:
            Similarity score (0-1)
        """
        if not schema.fields:
            return 0.0
        
        similarities = []
        weights = []
        
        for field in schema.fields:
            field_name = field.name
            
            user_value = user_data.get(field_name)
            candidate_value = candidate_data.get(field_name)
            
            if user_value is None or candidate_value is None:
                continue
            
            # Calculate similarity based on field type
            if field.type in ["integer", "decimal"]:
                try:
                    user_num = float(user_value)
                    candidate_num = float(candidate_value)
                    
                    # Normalize to 0-1 range
                    # Use relative difference
                    if user_num == 0:
                        similarity = 1.0 if candidate_num == 0 else 0.0
                    else:
                        diff = abs(candidate_num - user_num) / abs(user_num)
                        similarity = max(0.0, 1.0 - diff)  # Closer = higher similarity
                    
                    # Weight by field importance (required fields have higher weight)
                    weight = 2.0 if field.required else 1.0
                    
                    similarities.append(similarity)
                    weights.append(weight)
                except (ValueError, TypeError):
                    pass
            else:
                # Text/boolean: exact match = 1.0, otherwise 0.0
                similarity = 1.0 if user_value == candidate_value else 0.0
                weight = 2.0 if field.required else 1.0
                similarities.append(similarity)
                weights.append(weight)
        
        if not similarities:
            return 0.0
        
        # Weighted average
        weighted_sum = sum(s * w for s, w in zip(similarities, weights))
        total_weight = sum(weights)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    async def _calculate_semantic_similarity(self, user_product_name: str, candidate_product_name: str) -> float:
        """
        Calculate semantic similarity using OpenAI embeddings via OpenRouter (40% weight)
        
        Args:
            user_product_name: User product name
            candidate_product_name: Candidate product name
            
        Returns:
            Similarity score (0-1)
        """
        try:
            # Get embeddings using OpenAI model via OpenRouter
            user_response = await self.openrouter_client.embeddings.create(
                model=self.embedding_model,
                input=user_product_name,
                extra_headers={
                    "HTTP-Referer": "https://competitive-edge-engine.com",
                    "X-Title": "Competitive Edge Engine"
                }
            )
            candidate_response = await self.openrouter_client.embeddings.create(
                model=self.embedding_model,
                input=candidate_product_name,
                extra_headers={
                    "HTTP-Referer": "https://competitive-edge-engine.com",
                    "X-Title": "Competitive Edge Engine"
                }
            )
            
            user_embedding = user_response.data[0].embedding
            candidate_embedding = candidate_response.data[0].embedding
            
            # Calculate cosine similarity manually
            dot_product = sum(a * b for a, b in zip(user_embedding, candidate_embedding))
            norm_user = sum(a * a for a in user_embedding) ** 0.5
            norm_candidate = sum(b * b for b in candidate_embedding) ** 0.5
            
            similarity = dot_product / (norm_user * norm_candidate) if (norm_user * norm_candidate) > 0 else 0
            
            # Normalize to 0-1 range (cosine similarity is already -1 to 1)
            normalized_similarity = (similarity + 1) / 2
            
            return normalized_similarity
        except Exception as e:
            # Fallback: Use Gemini Flash Lite for text-based similarity if embeddings fail
            try:
                prompt = f"""Rate the similarity between these two product names on a scale of 0.0 to 1.0, where 1.0 means they are the same product and 0.0 means completely different products.

Product 1: {user_product_name}
Product 2: {candidate_product_name}

Return only a number between 0.0 and 1.0, no explanation."""
                
                response = await self.openrouter_client.chat.completions.create(
                    model="google/gemini-flash-1.5",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    extra_headers={
                        "HTTP-Referer": "https://competitive-edge-engine.com",
                        "X-Title": "Competitive Edge Engine"
                    }
                )
                
                similarity_text = response.choices[0].message.content.strip()
                # Extract number from response
                import re
                match = re.search(r'0?\.\d+|1\.0|0', similarity_text)
                if match:
                    similarity = float(match.group())
                    return max(0.0, min(1.0, similarity))  # Clamp to 0-1
            except Exception:
                pass
            
            # Final fallback: simple string similarity
            return 0.5
    
    async def calculate_confidence_score(
        self,
        user_product_name: str,
        user_data: Dict[str, Any],
        candidate_product_name: str,
        candidate_data: Dict[str, Any],
        schema: ProductSchema
    ) -> Dict[str, float]:
        """
        Calculate confidence score for a match candidate
        
        Args:
            user_product_name: User product name
            user_data: User product data
            candidate_product_name: Candidate product name
            candidate_data: Candidate product data
            schema: Product schema
            
        Returns:
            Dictionary with confidence_score, spec_similarity, semantic_similarity
        """
        # Calculate spec similarity (60%)
        spec_similarity = self._calculate_spec_similarity(user_data, candidate_data, schema)
        
        # Calculate semantic similarity (40%)
        semantic_similarity = await self._calculate_semantic_similarity(user_product_name, candidate_product_name)
        
        # Combined confidence score
        confidence_score = (0.6 * spec_similarity) + (0.4 * semantic_similarity)
        
        return {
            "confidence_score": confidence_score,
            "spec_similarity": spec_similarity,
            "semantic_similarity": semantic_similarity
        }

