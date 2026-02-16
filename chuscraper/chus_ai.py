from typing import Any, Optional, Type, cast
from pydantic import BaseModel
from .core.tab import Tab
from . import ai

async def extract(
    tab: Tab,
    prompt: str,
    schema: Optional[Type[BaseModel]] = None,
    provider: Optional[Any] = None,
) -> Any:
    """
    Extracts structured data from the current page content using AI.
    
    :param tab: The browser tab to extract from.
    :param prompt: Natural language instruction (e.g., "Extract product names and prices").
    :param schema: Pydantic model class for structured data.
    :param provider: LLM provider (defaults to Gemini if GEMINI_API_KEY is set).
    """
    # Get full HTML robustly
    html = await tab.evaluate("document.documentElement.outerHTML")
    if not html:
         # Fallback or wait? Let's try to wait if it's completely empty
         await tab.sleep(1)
         html = await tab.evaluate("document.documentElement.outerHTML")

    return await ai.extract(
        html=cast(str, html), prompt=prompt, schema=schema, provider=provider
    )

async def ask(tab: Tab, query: str, provider: Optional[Any] = None) -> str:
    """
    Answers a question about the current page content using AI.

    :param tab: The browser tab to query.
    :param query: Natural language question (e.g., "What is the check-in time?").
    :param provider: LLM provider.
    """
    html = await tab.evaluate("document.documentElement.outerHTML")
    return await ai.ask(html=cast(str, html), query=query, provider=provider)

async def pilot(tab: Tab, goal: str, max_steps: int = 10, provider: Optional[Any] = None) -> bool:
    """
    Runs an autonomous agent loop to achieve a goal in the given tab.
    
    :param tab: The browser tab to control.
    :param goal: Natural language goal.
    :param max_steps: Maximum steps before giving up.
    :param provider: LLM provider.
    """
    pilot = ai.AIPilot(tab, provider=provider)
    return await pilot.run(goal, max_steps=max_steps)

async def visual_extract(tab: Tab, prompt: str, schema: Optional[Type[BaseModel]] = None, provider: Optional[Any] = None) -> Any:
    """
    Extracts data using screenshots (Vision). 
    Useful when HTML is messy or contents are in Canvas/Images.

    :param tab: The browser tab to capture.
    :param prompt: Instruction for extraction.
    :param schema: Pydantic model for structured data.
    :param provider: LLM provider (must support vision).
    """
    vision = ai.VisionScraper(tab, provider=provider)
    return await vision.extract(prompt, schema=schema)

async def learn_selector(tab: Tab, description: str, provider: Optional[Any] = None) -> str:
    """
    Learns a robust CSS/Xpath selector for an element described in natural language.
    
    :param tab: The browser tab.
    :param description: Description of the element (e.g., "The blue signup button in the header").
    :param provider: LLM provider.
    """
    gen = ai.SelectorGenerator(tab, provider=provider)
    return await gen.learn(description)
