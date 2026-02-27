import os
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class SelectorGenerator:
    """
    Generates CSS selectors using LLMs.
    Isolated module - does not depend on core Browser/Crawler logic.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("Please install 'openai' to use SelectorGenerator")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model

    async def generate(self, html_snippet: str, target_fields: List[str]) -> Dict[str, str]:
        """
        Generates selectors for the given fields based on HTML.
        :param html_snippet: Representative HTML (e.g. one product card or article body).
        :param target_fields: List of fields to extract (e.g. ['price', 'title']).
        :return: Dict of field -> css_selector
        """
        system_prompt = "You are a CSS Selector expert. Return ONLY a JSON object mapping fields to selectors."

        user_prompt = f"""
        HTML Snippet:
        {html_snippet[:10000]}

        Target Fields: {target_fields}

        Return JSON format: {{ "field": "css_selector" }}
        Prefer classes and IDs over structural (nth-child) selectors.
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Selector Generation Failed: {e}")
            return {}
