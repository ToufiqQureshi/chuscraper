"""
Data extraction utilities for lead scraping.

Extractors for:
- Markdown conversion
- Structured data extraction
"""

from .markdown import html_to_markdown
from .structured import StructuredExtractor

__all__ = [
    'html_to_markdown',
    'StructuredExtractor',
]
