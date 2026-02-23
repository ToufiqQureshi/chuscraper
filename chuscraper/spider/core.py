import asyncio
import logging
from typing import List, Dict, Optional, Set, Callable
from urllib.parse import urlparse, urljoin
from chuscraper.core.tab import Tab
from chuscraper.core.browser import Browser

logger = logging.getLogger(__name__)

class Crawler:
    """
    A Universal Crawler that navigates a website, extracts content, and follows links.
    Features:
    - BFS (Breadth-First Search) Traversal
    - Concurrency (Multiple Tabs)
    - Domain Restriction (Stays on the same site)
    - Structured Output (Markdown, Metadata)
    """

    def __init__(
        self,
        start_urls: List[str] | str,
        max_pages: int = 10,
        max_depth: int = 2,
        concurrency: int = 2,
        browser_config: Optional[Dict] = None,
        extraction_hook: Optional[Callable[[Tab], Dict]] = None
    ):
        """
        :param start_urls: Single URL or list of URLs to start crawling from.
        :param max_pages: Maximum number of unique pages to crawl.
        :param max_depth: Maximum depth to traverse from the start URL.
        :param concurrency: Number of concurrent tabs to use.
        :param browser_config: Configuration dictionary for Browser.create().
        :param extraction_hook: A custom async function that takes a Tab and returns a dict of data.
                                If None, defaults to extracting title, url, and markdown.
        """
        if isinstance(start_urls, str):
            self.start_urls = [start_urls]
        else:
            self.start_urls = start_urls

        self.max_pages = max_pages
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.browser_config = browser_config or {}
        self.extraction_hook = extraction_hook

        self.visited: Set[str] = set()
        self.queue: asyncio.Queue = asyncio.Queue()
        self.results: List[Dict] = []
        self._browser: Optional[Browser] = None

    async def _worker(self, worker_id: int):
        """
        A worker that picks URLs from the queue and processes them using a Tab.
        """
        while len(self.visited) < self.max_pages:
            try:
                # Get a URL from the queue (non-blocking if empty, handled by timeout)
                current_url, depth = await asyncio.wait_for(self.queue.get(), timeout=2.0)
            except (asyncio.TimeoutError, asyncio.QueueEmpty):
                # If queue is empty and no active workers, we might be done.
                # In a real crawler, we'd need more robust termination logic.
                break

            if depth > self.max_depth:
                self.queue.task_done()
                continue

            if current_url in self.visited:
                self.queue.task_done()
                continue

            self.visited.add(current_url)
            logger.info(f"[Worker-{worker_id}] Crawling: {current_url} (Depth: {depth})")

            page = None
            try:
                # Open a new tab for this task using browser.get(new_tab=True)
                # The browser.new_tab method does not exist, use browser.get(new_tab=True) instead
                page = await self._browser.get(current_url, new_tab=True)

                # Wait for load - simplified
                await page.sleep(2)

                # Extract Data
                data = {}
                if self.extraction_hook:
                    # User provided hook
                    data = await self.extraction_hook(page)
                else:
                    # Default Extraction
                    data = {
                        "url": page.url,
                        "title": await page.evaluate("document.title"),
                        "markdown": await page.markdown()
                    }

                self.results.append(data)

                # Extract Links for Next Depth
                if depth < self.max_depth:
                    links = await page.get_all_urls(absolute=True)
                    base_domain = urlparse(self.start_urls[0]).netloc # Simple domain restriction

                    for link in links:
                        # Basic filtering: Same domain, http/s only
                        parsed_link = urlparse(link)
                        if parsed_link.netloc == base_domain and parsed_link.scheme in ("http", "https"):
                            if link not in self.visited:
                                await self.queue.put((link, depth + 1))

                # Close the tab after processing
                await page.close()

            except Exception as e:
                logger.error(f"[Worker-{worker_id}] Failed to process {current_url}: {e}")
                if page:
                    try:
                        await page.close()
                    except:
                        pass
            finally:
                self.queue.task_done()

    async def run(self) -> List[Dict]:
        """
        Starts the crawling process.
        """
        # Initialize Browser
        # We need to import here to avoid circular dependency issues if any, though standard import is fine.
        from chuscraper.core.browser import Browser

        # Enqueue start URLs
        for url in self.start_urls:
            await self.queue.put((url, 0))

        # Start Browser
        self._browser = await Browser.create(**self.browser_config)

        try:
            # Create workers
            workers = [asyncio.create_task(self._worker(i)) for i in range(self.concurrency)]

            # Wait for queue to be fully processed or max pages reached
            # We use a mix of join() and checking visited count in workers
            await self.queue.join()

            # Cancel workers (they might be waiting on queue.get)
            for w in workers:
                w.cancel()

            # Wait for cancellation to complete
            await asyncio.gather(*workers, return_exceptions=True)

        finally:
            if self._browser:
                await self._browser.stop()

        return self.results
