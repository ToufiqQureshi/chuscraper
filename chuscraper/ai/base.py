from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

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
        :param schema: (Optional) JSON Schema or Pydantic model dict to enforce structure.
        :return: A dictionary containing the extracted data.
        """
        pass
