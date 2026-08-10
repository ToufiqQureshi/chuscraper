"""
Robust HTML to Markdown conversion for Chuscraper.
Designed to produce "LLM-Ready" markdown by removing clutter.
"""

import re
import logging
from bs4 import BeautifulSoup
import html2text

logger = logging.getLogger(__name__)


class MarkdownConversionError(RuntimeError):
    """Raised when HTML could not be converted to Markdown."""


class MarkdownConverter:
    def __init__(self, ignore_links: bool = False, ignore_images: bool = False):
        self.ignore_links = ignore_links
        self.ignore_images = ignore_images

        # Tags to exclude completely (noise)
        self.excluded_tags = [
            'script', 'style', 'noscript', 'iframe', 'svg',
            'footer', 'nav', 'header', 'form', 'button',
            'input', 'select', 'textarea'
        ]

    def _new_h2t(self) -> "html2text.HTML2Text":
        """
        Build a fresh converter per call.

        HTML2Text carries parse state between handle() calls, so reusing one
        instance leaks list/table context from the previous document into the
        next one.
        """
        h2t = html2text.HTML2Text()
        h2t.ignore_links = self.ignore_links
        h2t.ignore_images = self.ignore_images
        h2t.ignore_emphasis = False
        h2t.body_width = 0  # No wrapping
        h2t.protect_links = True
        h2t.unicode_snob = True
        return h2t

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

                self._drop_empty_elements(soup)

                # Identify "Main Content" (heuristic).
                # <main> is unique per document, but <article> is not: listing
                # and blog-index pages have one per card, so taking only the
                # first threw away nearly the whole page. Keep them all.
                main_content = soup.find('main')
                if main_content:
                    html_content = str(main_content)
                else:
                    articles = soup.find_all('article')
                    if articles:
                        html_content = "\n".join(str(a) for a in articles)
                    else:
                        html_content = str(soup.body) if soup.body else str(soup)

            markdown = self._new_h2t().handle(html_content)

            # Post-processing cleanup
            markdown = self._cleanup_markdown(markdown)
            return markdown

        except Exception as e:
            # Never return the error text as if it were page content - that lands
            # in crawler output and downstream datasets as a real document.
            logger.error(f"Markdown conversion failed: {e}", exc_info=True)
            raise MarkdownConversionError(str(e)) from e

    #: elements that carry meaning even with no text of their own
    _MEANINGFUL_EMPTY = frozenset({
        'img', 'br', 'hr', 'picture', 'source', 'svg', 'video', 'audio',
        'embed', 'object', 'canvas', 'iframe', 'td', 'th', 'input',
    })

    def _drop_empty_elements(self, soup) -> None:
        """
        Strip elements that contain neither text nor meaningful media.

        The old version removed any element whose text was empty, which deleted
        every image wrapper - `<div><img></div>`, image-only links, figures -
        along with the images inside them.
        """
        # Deepest-first so a parent is judged after its children are resolved.
        for element in reversed(soup.find_all()):
            if element.name in self._MEANINGFUL_EMPTY:
                continue
            if element.get_text(strip=True):
                continue
            # Keep it if it still wraps something that renders.
            if element.find(lambda t: t.name in self._MEANINGFUL_EMPTY):
                continue
            element.extract()

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
