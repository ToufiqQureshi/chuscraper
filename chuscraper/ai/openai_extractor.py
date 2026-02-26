import os
import json
import logging
from typing import Dict, Any, Optional
from .base import BaseExtractor

logger = logging.getLogger(__name__)

class OpenAIExtractor(BaseExtractor):
    """
    Extractor using OpenAI's Chat Completion API.
    Requires 'openai' package installed.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("Please install 'openai' to use OpenAIExtractor: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API Key is required. Pass it to constructor or set OPENAI_API_KEY env var.")

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model

    async def extract(self, content: str, prompt: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extracts data using OpenAI.
        """
        system_prompt = "You are a helpful data extraction assistant. You extract structured JSON data from the provided text."

        user_prompt = f"""
        Task: {prompt}

        Content:
        {content[:20000]}
        """
        # Truncated content to avoid token limits for now. Ideally we use a token counter.

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )

            result = response.choices[0].message.content
            return json.loads(result)
        except Exception as e:
            logger.error(f"AI Extraction Failed: {e}")
            return {"error": str(e)}
