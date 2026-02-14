from typing import Optional, TYPE_CHECKING
from .providers import AIProvider, GeminiProvider

if TYPE_CHECKING:
    from ..core.tab import Tab

class SelectorGenerator:
    def __init__(self, tab: "Tab", provider: Optional[AIProvider] = None):
        self.tab = tab
        self.provider = provider or GeminiProvider()

    async def learn(self, description: str) -> str:
        """
        Learns the best CSS/Xpath selector for a given description.
        Returns a robust selector string.
        """
        html = await self.tab.evaluate("document.documentElement.outerHTML")
        
        prompt = f"""
Find the most robust CSS selector for the following element: "{description}"
Analyze the HTML structure and find a selector that won't break easily.

CONTENT:
{html[:15000]} # Truncated for token limit

Return ONLY the selector string (no markdown, no quotes).
Example: 
div.hotel-card > h3.title
"""
        selector = await self.provider.generate_response(prompt)
        return selector.strip()
