from __future__ import annotations
from .base import TabMixin
from typing import TYPE_CHECKING, List
import urllib.parse
from ...extractors.markdown import html_to_markdown
from ... import cdp
from .. import element

if TYPE_CHECKING:
    from ..tab import Tab
    from ..element import Element

class ExtractionMixin(TabMixin):
    async def get_content(self) -> str:
        """
        gets the current page source content (html)
        :return:
        :rtype:
        """
        doc: cdp.dom.Node = await self.send(cdp.dom.get_document(-1, True))
        return await self.send(
            cdp.dom.get_outer_html(backend_node_id=doc.backend_node_id)
        )

    async def markdown(self) -> str:
        """
        Converts the current page content to clean, LLM-ready Markdown.
        """
        content = await self.get_content()
        return html_to_markdown(content)

    async def get_all_linked_sources(self) -> List[Element]:
        """
        get all elements of tag: link, a, img, scripts meta, video, audio

        :return:
        """
        all_assets = await self.tab.query_selector_all(selector="a,link,img,script,meta")
        return [element.create(asset.node, self.tab) for asset in all_assets]

    async def get_all_urls(self, absolute: bool = True) -> List[str]:
        """
        convenience function, which returns all links (a,link,img,script,meta)

        :param absolute: try to build all the links in absolute form instead of "as is", often relative
        :return: list of urls
        """
        res: list[str] = []
        all_assets = await self.tab.query_selector_all(selector="a,link,img,script,meta")
        for asset in all_assets:
            if not absolute:
                res_to_add = asset.src or asset.href
                if res_to_add:
                    res.append(res_to_add)
            else:
                for k, v in asset.attrs.items():
                    if k in ("src", "href"):
                        if "#" in v:
                            continue
                        if not any([_ in v for _ in ("http", "//", "/")]):
                            continue
                        abs_url = urllib.parse.urljoin(
                            "/".join(self.tab.url.rsplit("/")[:3] if self.tab.url else []), v
                        )
                        if not abs_url.startswith(("http", "//", "ws")):
                            continue
                        res.append(abs_url)
        return res

    async def crawl(self, depth: int = 1, max_pages: int = 5) -> List[str]:
        """
        Simple crawler that visits links on the current page.

        Args:
            depth: How deep to crawl (currently only supports 1 - shallow crawl of links on current page)
            max_pages: Limit number of pages to visit

        Returns:
            List of visited URLs
        """
        # TODO: Implement full recursive crawler with queue
        # For now, implemented a "map" feature essentially
        links = await self.get_all_urls()

        # Filter external links?
        current_host = urllib.parse.urlparse(self.tab.url).hostname

        visited = []
        count = 0
        for link in links:
            if count >= max_pages:
                break
            if urllib.parse.urlparse(link).hostname == current_host:
                visited.append(link)
                # In a real crawler, we would navigate here and extract
                count += 1

        return visited
