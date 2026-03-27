import os
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

async def generate_selectors(html_snippet: str, target_fields: List[str], api_key: Optional[str] = None, model: str = "gpt-4o") -> Dict[str, str]:
    """
    Generates robust CSS selectors for the given fields from an HTML snippet using OpenAI.

    This function analyzes the HTML structure and returns the most reliable CSS selectors
    to extract the requested fields (e.g., 'price', 'title').

    :param html_snippet: A representative HTML string (e.g. product card or article body).
    :param target_fields: List of fields to generate selectors for.
    :param api_key: OpenAI API Key (optional, defaults to env var).
    :param model: Model to use (default: gpt-4o).
    :return: Dictionary mapping field names to CSS selectors.
    """
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ImportError("Please install 'openai' to use selector generation: pip install openai")

    final_api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not final_api_key:
        raise ValueError("OpenAI API Key is required. Set OPENAI_API_KEY env var or pass it explicitly.")

    client = AsyncOpenAI(api_key=final_api_key)

    system_prompt = "You are a CSS Selector expert. Return ONLY a valid JSON object mapping fields to selectors."

    user_prompt = f"""
    HTML Snippet:
    {html_snippet[:15000]}

    Target Fields: {target_fields}

    Task: Identify the most robust CSS selector for each target field.
    Prefer semantic classes and IDs. Avoid brittle nth-child chains if possible.

    Output Format:
    {{
        "field_name": "css_selector"
    }}
    """

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        result = response.choices[0].message.content
        return json.loads(result)
    except Exception as e:
        logger.error(f"Selector Generation Failed: {e}")
        return {"error": str(e)}
