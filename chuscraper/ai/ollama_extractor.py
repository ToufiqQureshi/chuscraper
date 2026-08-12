import logging
import json
from typing import Dict, Any, Optional
from .base import BaseExtractor, normalize_schema

logger = logging.getLogger(__name__)

class OllamaExtractor(BaseExtractor):
    """
    Extractor using local Ollama instance (default: http://localhost:11434).
    Requires 'ollama' package installed.
    """

    def __init__(self, model: str = "llama3", host: str = "http://localhost:11434", content_limit: int = 15000):
        try:
            import ollama
        except ImportError:
            raise ImportError("Please install 'ollama' to use OllamaExtractor: pip install ollama")

        self.client = ollama.Client(host=host)
        self.model = model
        self.content_limit = content_limit

    async def extract(self, content: str, prompt: str, schema: Optional[Any] = None) -> Dict[str, Any]:
        """
        Extracts data using local Ollama model.

        When `schema` is supplied (JSON Schema dict or Pydantic model) it is
        passed to Ollama as a structured-output format, and also embedded in the
        prompt so older Ollama builds still honour it.
        """
        import asyncio

        system_prompt = "You are a data extraction assistant. Output only valid JSON."
        json_schema = normalize_schema(schema)
        user_prompt = self.build_prompt(content, prompt, json_schema, self.content_limit)

        # Ollama >= 0.5 accepts a JSON Schema here; older builds only know 'json'.
        fmt: Any = json_schema if json_schema else 'json'

        try:
            # Ollama client is sync, so run in thread
            def _call_ollama():
                try:
                    return self.client.chat(
                        model=self.model,
                        messages=[
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': user_prompt},
                        ],
                        format=fmt
                    )
                except Exception:
                    if fmt == 'json':
                        raise
                    logger.debug("Ollama rejected schema format; retrying with plain json mode.")
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
