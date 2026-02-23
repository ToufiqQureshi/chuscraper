from re import sub as re_sub
from chuscraper.engine.parser import Selector, Selectors
from chuscraper.engine.core.custom_types import TextHandler
from chuscraper.engine.core._types import (
    Dict, Any, cast, Optional, Generator, extraction_types,
)

class Convertor:
    """Utils for extraction and conversion"""

    _extension_map: Dict[str, extraction_types] = {
        "md": "markdown",
        "html": "html",
        "txt": "text",
    }

    @classmethod
    def _convert_to_markdown(cls, body: str) -> str:
        """Convert HTML content to Markdown"""
        from markdownify import markdownify
        return markdownify(body)

    @classmethod
    def _extract_content(
        cls,
        page: Selector,
        extraction_type: extraction_types = "markdown",
        css_selector: Optional[str] = None,
        main_content_only: bool = False,
    ) -> Generator[str, None, None]:
        """Extract the content of a Selector"""
        if not page or not isinstance(page, Selector):
            raise TypeError("Input must be of type `Selector`")
        elif not extraction_type or extraction_type not in cls._extension_map.values():
            raise ValueError(f"Unknown extraction type: {extraction_type}")
        else:
            if main_content_only:
                page = cast(Selector, page.css("body").first) or page

            pages = [page] if not css_selector else cast(Selectors, page.css(css_selector))
            for p in pages:
                if extraction_type == "markdown":
                    yield cls._convert_to_markdown(str(p.html_content))
                elif extraction_type == "html":
                    yield str(p.html_content)
                elif extraction_type == "text":
                    txt_content = p.get_all_text(strip=True)
                    for s in ("\n", "\r", "\t", " "):
                        txt_content = TextHandler(re_sub(f"[{s}]+", s, txt_content))
                    yield str(txt_content)
            yield ""
