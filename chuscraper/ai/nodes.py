import re
from typing import List, Optional

class AINodes:
    @staticmethod
    def clean_html(html: str) -> str:
        """
        Cleans HTML for the LLM.
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("Please install 'beautifulsoup4' to use AI cleaning features. Run: pip install chuscraper[ai]")
            
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove useless tags for extraction
        for tag in soup(["script", "style", "path", "svg", "noscript", "iframe"]):
            tag.decompose()
            
        # Optional: Flatten nested structures if they don't carry info
        # But for MMT, we want to keep some hierarchy
        
        text = soup.get_text(separator=" ", strip=True)
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text)
        
        # If we want a mix of text and some HTML for context:
        # return soup.prettify()[:10000] # Simple truncation for now
        return text

    @staticmethod
    def chunk_content(content: str, max_tokens: int = 15000) -> List[str]:
        """Simple chunking logic if the page is too huge."""
        # For now, we assume Gemini-1.5-Flash can handle 1M tokens, 
        # so we don't chunk unless it's extreme.
        if len(content) < max_tokens * 4:
            return [content]
        
        return [content[i:i + max_tokens * 4] for i in range(0, len(content), max_tokens * 4)]
