from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


def normalize_schema(schema: Optional[Any]) -> Optional[Dict]:
    """
    Coerce whatever the caller passed into a plain JSON Schema dict.

    Accepts a Pydantic model class/instance, a dataclass-ish object exposing
    ``model_json_schema()`` / ``schema()``, or an already-plain dict. Returns
    None when there is nothing usable, so callers can just skip schema handling.
    """
    if schema is None:
        return None
    if isinstance(schema, dict):
        return schema
    for attr in ("model_json_schema", "schema"):
        fn = getattr(schema, attr, None)
        if callable(fn):
            try:
                result = fn()
                if isinstance(result, dict):
                    return result
            except Exception:
                continue
    return None


class BaseExtractor(ABC):
    """
    Abstract base class for AI Extractors.
    """

    @abstractmethod
    async def extract(self, content: str, prompt: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extracts structured data from content using an AI model.

        :param content: The raw text/markdown content to process.
        :param prompt: The instruction for the AI (e.g., "Extract prices").
        :param schema: (Optional) JSON Schema dict or Pydantic model to enforce structure.
        :return: A dictionary containing the extracted data.
        """
        pass

    @staticmethod
    def build_prompt(content: str, prompt: str, schema: Optional[Dict], limit: int) -> str:
        """Compose the user prompt, including the schema contract when given."""
        if len(content) > limit:
            # Say so rather than silently dropping the tail of the page.
            import logging
            logging.getLogger(__name__).warning(
                "Content is %d chars, truncating to %d for the model. "
                "Pass a larger `content_limit` or pre-slice the page to avoid this.",
                len(content), limit,
            )
            content = content[:limit]

        parts = [f"Task: {prompt}"]
        if schema:
            import json
            parts.append(
                "Return JSON conforming exactly to this JSON Schema. Use only the "
                "properties it declares, with the declared types:\n"
                + json.dumps(schema, indent=2)
            )
        parts.append(f"Content:\n{content}")
        return "\n\n".join(parts)
