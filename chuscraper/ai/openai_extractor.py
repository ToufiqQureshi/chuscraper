import os
import json
import logging
from typing import Dict, Any, Optional
from .base import BaseExtractor, normalize_schema

logger = logging.getLogger(__name__)

class OpenAIExtractor(BaseExtractor):
    """
    Extractor using OpenAI's Chat Completion API.
    Requires 'openai' package installed.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", content_limit: int = 20000):
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("Please install 'openai' to use OpenAIExtractor: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API Key is required. Pass it to constructor or set OPENAI_API_KEY env var.")

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model
        self.content_limit = content_limit

    async def extract(self, content: str, prompt: str, schema: Optional[Any] = None) -> Dict[str, Any]:
        """
        Extracts data using OpenAI.

        When `schema` is supplied (a JSON Schema dict or a Pydantic model) it is
        enforced via structured outputs, falling back to embedding the schema in
        the prompt if the model/endpoint rejects json_schema mode.
        """
        system_prompt = "You are a helpful data extraction assistant. You extract structured JSON data from the provided text."

        json_schema = normalize_schema(schema)
        user_prompt = self.build_prompt(content, prompt, json_schema, self.content_limit)

        response_format: Dict[str, Any] = {"type": "json_object"}
        if json_schema:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "extraction",
                    "strict": False,
                    "schema": json_schema,
                },
            }

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format=response_format,
                )
            except Exception as e:
                if response_format["type"] != "json_schema":
                    raise
                # Older models / proxies don't know json_schema mode; the schema
                # is already in the prompt, so plain JSON mode still works.
                logger.debug(f"Structured output unsupported ({e}); falling back to json_object.")
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                )

            result = response.choices[0].message.content
            return json.loads(result)
        except Exception as e:
            logger.error(f"AI Extraction Failed: {e}")
            return {"error": str(e)}
