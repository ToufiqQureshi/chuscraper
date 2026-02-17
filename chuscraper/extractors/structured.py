"""
Structured Data Extraction using LLMs.
Similar to instructor/marvin but integrated with Chuscraper's context.
"""

import json
import logging
from typing import Type, TypeVar, Optional
from pydantic import BaseModel

from ..ai.providers import AIProvider, GeminiProvider

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class StructuredExtractor:
    def __init__(self, provider: Optional[AIProvider] = None):
        self.provider = provider or GeminiProvider()

    async def extract(self, text: str, schema: Type[T]) -> T:
        """
        Extracts structured data from text/markdown based on a Pydantic schema.
        """
        schema_json = json.dumps(schema.model_json_schema(), indent=2)

        prompt = f"""
You are a precise data extraction engine.
Extract the following data from the provided content.

TARGET SCHEMA (JSON Schema):
{schema_json}

CONTENT:
{text[:50000]}

INSTRUCTIONS:
1. Return ONLY valid JSON matching the schema.
2. If data is missing, use null or defaults.
3. Do not invent information.
"""
        response = await self.provider.generate_response(prompt, json_mode=True)

        try:
            # Clean response if it contains markdown code blocks
            clean_json = response
            if "```json" in response:
                clean_json = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                clean_json = response.split("```")[1].split("```")[0].strip()

            data = json.loads(clean_json)
            return schema.model_validate(data)
        except Exception as e:
            logger.error(f"Structured extraction failed: {e}")
            logger.debug(f"Raw Response: {response}")
            raise ValueError(f"Failed to parse LLM response into {schema.__name__}: {e}")
