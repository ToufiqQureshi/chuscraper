import asyncio
import logging
from typing import List, Dict, Optional, Set, Callable, Any
from urllib.parse import urlparse, urljoin, urldefrag
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
    - AI Extraction Hook (Placeholder)
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

        # Calculate allowed domains (strip www. prefix)
        self.allowed_domains = set()
        for url in self.start_urls:
            domain = urlparse(url).netloc
            if domain.startswith("www."):
                domain = domain[4:]
            self.allowed_domains.add(domain)

    def _is_allowed(self, url: str) -> bool:
        """Checks if the URL belongs to the allowed domains."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False

            domain = parsed.netloc
            if domain.startswith("www."):
                domain = domain[4:]

            return domain in self.allowed_domains
        except Exception:
            return False

    def _normalize_url(self, url: str) -> str:
        """Removes fragments and normalizes URL."""
        url, _ = urldefrag(url)
        # Ensure trailing slash consistency? Maybe. For now, rely on standard form.
        return url

    async def _worker(self, worker_id: int):
        """
        A worker that picks URLs from the queue and processes them using a Tab.
        """
        while True:
            # Check exit condition FIRST
            # If we reached the page limit, we stop processing new pages.
            # However, we must continue to 'drain' the queue to satisfy queue.join() in run()
            # otherwise the main loop will hang forever waiting for task_done().
            if len(self.visited) >= self.max_pages:
                try:
                    # Non-blocking get to drain the queue
                    self.queue.get_nowait()
                    self.queue.task_done()
                except asyncio.QueueEmpty:
                    # If queue is empty and we are over limit, we can just wait/break
                    # But other workers might still be adding?
                    # If we break here, queue.join() waits for them.
                    # We'll rely on the timeout below to exit naturally if empty.
                    pass

                # Small sleep to avoid busy loop if queue fills up again
                await asyncio.sleep(0.1)

                # We can try to break if we are sure no one is adding...
                # But safer to just continue draining loop until cancelled or queue empty check in run() logic?
                # Actually, if all workers enter this state, the queue will eventually empty and join() returns.
                # Then workers are cancelled.
                continue

            try:
                # Get a URL from the queue (non-blocking if empty, handled by timeout)
                # We use a short timeout so we can periodically check the visited limit
                queue_item = await asyncio.wait_for(self.queue.get(), timeout=2.0)
                current_url, depth = queue_item
            except (asyncio.TimeoutError, asyncio.QueueEmpty):
                # If queue is empty for a while, we assume we are done
                break

            if depth > self.max_depth:
                self.queue.task_done()
                continue

            # Check visited again in case another worker processed it
            if current_url in self.visited:
                self.queue.task_done()
                continue

            self.visited.add(current_url)
            logger.info(f"[Worker-{worker_id}] Crawling: {current_url} (Depth: {depth})")

            page = None
            try:
                # Open a new tab for this task using browser.get(new_tab=True)
                page = await self._browser.get(current_url, new_tab=True)

                # Wait for load - slightly increased to ensure scripts run
                await page.sleep(4)

                # Update URL after redirect (important!)
                final_url = self._normalize_url(page.url)
                if final_url != current_url:
                     self.visited.add(final_url)

                # Extract Data
                data = {}
                if self.extraction_hook:
                    # User provided hook
                    data = await self.extraction_hook(page)
                else:
                    # Default Extraction
                    try:
                        title = await page.evaluate("document.title")
                    except:
                        title = "No Title"

                    data = {
                        "url": final_url,
                        "title": title,
                        "markdown": await page.markdown()
                    }

                self.results.append(data)

                # Extract Links for Next Depth
                if depth < self.max_depth:
                    # Use get_all_urls with error handling
                    # Fallback to manual JS extraction if CDP fails
                    links = []
                    try:
                        links = await page.get_all_urls(absolute=True)
                    except Exception as e:
                        logger.warning(f"[Worker-{worker_id}] CDP link extraction failed: {e}")

                    if not links:
                        logger.debug(f"[Worker-{worker_id}] Fallback to JS link extraction")
                        try:
                            # Robust JS extraction that handles shadow DOM and relative links
                            js_links = await page.evaluate("""
                                Array.from(document.querySelectorAll('a[href]')).map(a => a.href)
                            """)
                            if js_links and isinstance(js_links, list):
                                links = js_links
                        except Exception as e:
                            logger.error(f"[Worker-{worker_id}] JS link extraction failed: {e}")

                    for link in links:
                        normalized_link = self._normalize_url(link)

                        if self._is_allowed(normalized_link):
                            if normalized_link not in self.visited:
                                await self.queue.put((normalized_link, depth + 1))
                                logger.debug(f"[Worker-{worker_id}] Added: {normalized_link}")
                        else:
                             logger.debug(f"[Worker-{worker_id}] Skipped external/invalid: {normalized_link}")

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

    async def run(self, prompt: Optional[str] = None, schema: Optional[Any] = None) -> List[Dict]:
        """
        Starts the crawling process.

        :param prompt: (Optional) Natural language prompt for AI extraction (Coming Soon)
        :param schema: (Optional) Pydantic model for structured extraction (Coming Soon)
        """
        # Initialize Browser
        from chuscraper.core.browser import Browser

        # Enqueue start URLs
        for url in self.start_urls:
            await self.queue.put((self._normalize_url(url), 0))

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
