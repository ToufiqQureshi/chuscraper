from .providers import GeminiProvider, OpenAIProvider, AIProvider
from .nodes import AINodes
from .schema import AISchemaHandler
from .agent import AIPilot
from .vision import VisionScraper
from .selector_gen import SelectorGenerator
from typing import Any, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    try:
        from pydantic import BaseModel
    except ImportError:
        BaseModel = Any

async def extract(
    html: str, 
    prompt: str, 
    schema: Optional[Type["BaseModel"]] = None,
    provider: Optional[AIProvider] = None
) -> Any:
    """
    Stand-alone AI extraction from HTML string.
    If provider is None, it tries to use Gemini via GEMINI_API_KEY.
    """
    if not provider:
        provider = GeminiProvider()
    
    # Clean HTML
    cleaned = AINodes.clean_html(html)
    
    # Wrap prompt with schema instructions
    final_prompt = AISchemaHandler.wrap_prompt(prompt, schema)
    
    # Generate
    response = await provider.generate_response(
        prompt=f"CONTENT:\n{cleaned}\n\nREQUEST: {final_prompt}",
        json_mode=(schema is not None)
    )
    
    if schema:
        return AISchemaHandler.validate_and_parse(response, schema)
    return response

async def ask(
    html: str, 
    query: str, 
    provider: Optional[AIProvider] = None
) -> str:
    """Answers a natural language question about the HTML content."""
    return await extract(html, query, provider=provider)
