import logging
import json
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

    async def extract(self, content: str, prompt: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extracts data using local Ollama model.
        """
        import asyncio

        system_prompt = "You are a data extraction assistant. Output only valid JSON."
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

            result = response['message']['content']
            return json.loads(result)
        except Exception as e:
            logger.error(f"Ollama Extraction Failed: {e}")
            return {"error": str(e)}
