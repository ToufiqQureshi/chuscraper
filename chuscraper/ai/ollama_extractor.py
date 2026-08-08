import logging
import json
import re
from typing import Dict, Any, Optional
from .base import BaseExtractor

logger = logging.getLogger(__name__)

class OllamaExtractor(BaseExtractor):
    """
    Extractor using local Ollama instance (default: http://localhost:11434).
    Requires 'ollama' package installed.
    """

    def __init__(self, model: str = "llama3", host: str = "http://localhost:11434"):
        try:
            import ollama
            self.client = ollama.Client(host=host)
        except ImportError:
            raise ImportError("Please install 'ollama' to use OllamaExtractor: pip install ollama")

        self.model = model

    def _clean_json(self, raw_text: str) -> str:
        """Removes code blocks and extracts JSON object."""
        # 1. Remove markdown code blocks
        if "```" in raw_text:
            match = re.search(r"```(?:json)?(.*?)```", raw_text, re.DOTALL)
            if match:
                raw_text = match.group(1)

        # 2. Find first '{' and last '}'
        start = raw_text.find("{")
        end = raw_text.rfind("}")

        if start != -1 and end != -1:
            return raw_text[start:end+1]

        return raw_text

    async def extract(self, content: str, prompt: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extracts data using local Ollama model.
        """
        import asyncio

        system_prompt = "You are a data extraction assistant. Output only valid JSON. Do not add any conversational text."
        user_prompt = f"Task: {prompt}\n\nContent:\n{content[:15000]}"

        try:
            # Ollama client is sync, so run in thread
            def _call_ollama():
                return self.client.chat(
                    model=self.model,
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt},
                    ],
                    format='json'
                )

            response = await asyncio.to_thread(_call_ollama)

            raw_result = response['message']['content']
            # Log for debugging if parsing fails
            # logger.debug(f"Ollama Raw Response: {raw_result}")

            clean_result = self._clean_json(raw_result)

            return json.loads(clean_result)
        except Exception as e:
            logger.error(f"Ollama Extraction Failed: {e}")
            # Consider adding raw_result to error if available?
            # For now, just logging is enough.
            return {"error": str(e)}
