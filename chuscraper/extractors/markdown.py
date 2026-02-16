"""
Robust HTML to Markdown conversion for Chuscraper.
Designed to produce "LLM-Ready" markdown by removing clutter.
"""

import re
import logging
from typing import Optional
from bs4 import BeautifulSoup
import html2text

logger = logging.getLogger(__name__)

class MarkdownConverter:
    def __init__(self, ignore_links: bool = False, ignore_images: bool = False):
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = ignore_links
        self.h2t.ignore_images = ignore_images
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # No wrapping
        self.h2t.protect_links = True
        self.h2t.unicode_snob = True

        # Tags to exclude completely (noise)
        self.excluded_tags = [
            'script', 'style', 'noscript', 'iframe', 'svg',
            'footer', 'nav', 'header', 'form', 'button',
            'input', 'select', 'textarea'
        ]

    def convert(self, html_content: str, clean_noise: bool = True) -> str:
        """
        Converts HTML to clean Markdown.
        """
        if not html_content:
            return ""

        try:
            if clean_noise:
                soup = BeautifulSoup(html_content, 'html.parser')

                # Remove unwanted tags
                for tag in self.excluded_tags:
                    for element in soup.find_all(tag):
                        element.decompose()

                # Remove empty elements
                for element in soup.find_all():
                    if len(element.get_text(strip=True)) == 0 and element.name not in ['img', 'br', 'hr']:
                        element.extract()

                # Identify "Main Content" (heuristic)
                # If <main> or <article> exists, prioritize it
                main_content = soup.find('main') or soup.find('article')
                if main_content:
                    html_content = str(main_content)
                else:
                    html_content = str(soup.body) if soup.body else str(soup)

            markdown = self.h2t.handle(html_content)

            # Post-processing cleanup
            markdown = self._cleanup_markdown(markdown)
            return markdown

        except Exception as e:
            logger.error(f"Markdown conversion failed: {e}")
            return f"Error converting to markdown: {e}"

    def _cleanup_markdown(self, text: str) -> str:
        """Remove excessive newlines and whitespace."""
        # Collapse multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        # Remove trailing whitespace
        text = "\n".join([line.rstrip() for line in text.splitlines()])
        return text.strip()

def html_to_markdown(html: str, clean: bool = True) -> str:
    converter = MarkdownConverter()
    return converter.convert(html, clean_noise=clean)
