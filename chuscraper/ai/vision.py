import base64
import io
from typing import Any, Dict, Optional, Type, TYPE_CHECKING
from .providers import AIProvider, GeminiProvider
from .schema import AISchemaHandler

if TYPE_CHECKING:
    from ..core.tab import Tab
    try:
        from pydantic import BaseModel
    except ImportError:
        BaseModel = Any

class VisionScraper:
    def __init__(self, tab: "Tab", provider: Optional[AIProvider] = None):
        self.tab = tab
        # Vision requires a multi-modal provider. Gemini 1.5 is default.
        self.provider = provider or GeminiProvider()

    async def extract(
        self, 
        prompt: str, 
        schema: Optional[Type["BaseModel"]] = None
    ) -> Any:
        """Extracts data using screenshots (Vision)."""
        screenshot_bytes = await self.tab.screenshot()
        
        # We need to modify GeminiProvider to handle image bytes if we want native vision.
        # But for now, let's assume the provider can take a list of parts or we use a specific method.
        # Since I'm using google-genai, it supports multi-modal.
        
        # Prepare the multi-modal prompt
        # We'll need to update providers.py to handle image input properly.
        
        final_prompt = AISchemaHandler.wrap_prompt(prompt, schema)
        
        # For now, let's assume we add generate_visual_response to the provider
        if hasattr(self.provider, "generate_visual_response"):
            response = await self.provider.generate_visual_response(
                prompt=f"Look at this screenshot and: {final_prompt}",
                image_bytes=screenshot_bytes
            )
        else:
            # Fallback (maybe text only if no vision support in provider yet)
            response = await self.provider.generate_response(
                f"VISION PROMPT (No image support yet): {final_prompt}"
            )

        if schema:
            return AISchemaHandler.validate_and_parse(response, schema)
        return response
