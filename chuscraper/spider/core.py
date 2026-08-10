import asyncio
import inspect
import logging
import json
import csv
from typing import List, Dict, Optional, Set, Callable, Any, Literal, Awaitable
from urllib.parse import urlparse, urldefrag
from chuscraper.core.tab import Tab
from chuscraper.core.browser import Browser

try:
    from chuscraper.ai.base import BaseExtractor
except ImportError:
    BaseExtractor = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

logger = logging.getLogger(__name__)

FormatType = Literal["markdown", "html", "text"]

class Crawler:
    """
    A Universal Crawler that navigates a website, extracts content, and follows links.
    Features:
    - BFS (Breadth-First Search) Traversal
    - Concurrency (Multiple Tabs)
    - Domain Restriction (Stays on the same site)
    - Structured Output (Markdown, Metadata, HTML, Text)
    - Streaming Callback (Memory Efficient)
    - File Output (JSON, CSV, JSONL, Markdown)
    - Sitemap Support
    - AI Extraction (LLM)
    """

    #: how deep nested <sitemapindex> chains are followed before giving up
    MAX_SITEMAP_DEPTH = 5

    def __init__(
        self,
        start_urls: List[str] | str | None = None,
        sitemap_url: str | None = None,
        max_pages: int = 10,
        max_depth: int = 2,
        concurrency: int = 2,
        formats: Optional[List[FormatType]] = None,
        browser_config: Optional[Dict] = None,
        extraction_hook: Optional[Callable[[Tab], Dict]] = None,
        on_page_crawled: Optional[Callable[[Dict], Awaitable[None]]] = None,
        extractor: Optional[Any] = None, # Expects BaseExtractor
        page_settle_time: float = 4.0,
    ):
        """
        :param start_urls: Single URL or list of URLs to start crawling from.
        :param sitemap_url: URL of the sitemap.xml to crawl. Overrides start_urls discovery.
        :param max_pages: Maximum number of unique pages to crawl.
        :param max_depth: Maximum depth to traverse from the start URL.
        :param concurrency: Number of concurrent tabs to use.
        :param formats: List of formats to extract: "markdown", "html", "text". Default: ["markdown"]
        :param browser_config: Configuration dictionary for Browser.create().
        :param extraction_hook: A custom async function that takes a Tab and returns a dict of data.
        :param on_page_crawled: A custom async callback function called for every crawled page.
                                Receives the data dict. Useful for streaming/saving to DB.
        :param extractor: An instance of `chuscraper.ai.BaseExtractor` (e.g. OpenAIExtractor) for structured extraction.
        :param page_settle_time: Seconds to wait after navigation before extracting,
                                 to let client-rendered content paint.
        """
        if sitemap_url:
            self.start_urls = []
            self.sitemap_url = sitemap_url
        elif start_urls:
            if isinstance(start_urls, str):
                self.start_urls = [start_urls]
            else:
                self.start_urls = start_urls
            self.sitemap_url = None
        else:
            raise ValueError("Either start_urls or sitemap_url must be provided.")

        self.max_pages = max_pages
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.formats = list(formats) if formats else ["markdown"]
        self.browser_config = browser_config or {}
        self.extraction_hook = extraction_hook
        self.on_page_crawled = on_page_crawled
        self.extractor = extractor
        self.page_settle_time = page_settle_time

        self.visited: Set[str] = set()
        self.queue: asyncio.Queue = asyncio.Queue()
        self.results: List[Dict] = []
        self._browser: Optional[Browser] = None
        # Guards the visited-set + max_pages check so N concurrent workers can't
        # all pass the budget check and overshoot max_pages.
        self._claim_lock = asyncio.Lock()

        # Calculate allowed domains (strip www. prefix)
        self.allowed_domains = set()

        # If sitemap is used, we determine domain from sitemap URL initially
        initial_urls = self.start_urls if self.start_urls else [self.sitemap_url]
        for url in initial_urls:
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
        return url

    async def _fetch_sitemap(self, url: str, _seen: Optional[Set[str]] = None, _depth: int = 0) -> List[str]:
        """Fetches and parses a sitemap (and nested sitemaps)."""
        # Sitemap indexes can point at each other (or at themselves); without a
        # seen-set + depth cap that is unbounded recursion.
        if _seen is None:
            _seen = set()
        if url in _seen or _depth > self.MAX_SITEMAP_DEPTH:
            logger.debug(f"Skipping already-seen or too-deep sitemap: {url}")
            return []
        _seen.add(url)

        logger.info(f"Fetching sitemap: {url}")
        urls = []
        page = None
        try:
            # FIX: Use browser.get(new_tab=True) instead of non-existent new_tab method
            page = await self._browser.get(url, new_tab=True)
            # Wait for content
            await page.sleep(2)
            content = await page.get_content()
            await page.close()
            page = None

            if not BeautifulSoup:
                logger.error("BeautifulSoup not installed. Cannot parse sitemap.")
                return []

            # Parse XML
            soup = BeautifulSoup(content, "xml")

            # Check for sitemap index
            sitemaps = soup.find_all("sitemap")
            if sitemaps:
                for sm in sitemaps:
                    loc = sm.find("loc")
                    if loc:
                        nested_urls = await self._fetch_sitemap(loc.text.strip(), _seen, _depth + 1)
                        urls.extend(nested_urls)

            # Check for urlset
            url_tags = soup.find_all("url")
            for url_tag in url_tags:
                loc = url_tag.find("loc")
                if loc:
                    clean_url = loc.text.strip()
                    urls.append(clean_url)

        except Exception as e:
            logger.error(f"Failed to fetch/parse sitemap {url}: {e}")
            if page:
                try:
                    await page.close()
                except:
                    pass

        return urls

    async def _extract_content(self, page: Tab, prompt: Optional[str] = None, schema: Optional[Any] = None) -> Dict[str, Any]:
        """Extracts content based on configured formats OR AI."""
        try:
            title = await page.evaluate("document.title")
        except:
            title = "No Title"

        data = {
            "url": self._normalize_url(page.url),
            "title": title,
        }

        # 1. Standard Formats Extraction
        content_markdown = ""
        if "markdown" in self.formats or (self.extractor and prompt): # AI needs markdown
            content_markdown = await page.markdown()
            if "markdown" in self.formats:
                data["markdown"] = content_markdown

        if "html" in self.formats:
            data["html"] = await page.get_content()

        if "text" in self.formats:
            try:
                data["text"] = await page.to_text()
            except AttributeError:
                 data["text"] = await page.evaluate("document.body.innerText")

        # 2. AI Extraction (If enabled and prompt provided)
        if self.extractor and prompt:
            logger.info(f"Extracting AI data for {data['url']}...")
            try:
                ai_data = await self.extractor.extract(content_markdown, prompt, schema)
                data["extracted_data"] = ai_data
            except Exception as e:
                logger.error(f"AI Extraction failed for {data['url']}: {e}")
                data["extracted_data"] = {"error": str(e)}

        return data

    async def _emit(self, data: Dict) -> None:
        """Hands a crawled page to the streaming callback, or stores it."""
        if not self.on_page_crawled:
            self.results.append(data)
            return

        try:
            result = self.on_page_crawled(data)
            # Support plain functions, async functions and anything awaitable.
            # Previously a sync callback silently dropped the page entirely.
            if inspect.isawaitable(result):
                await result
        except Exception as e:
            logger.error(f"Error in on_page_crawled callback: {e}")

    async def _claim(self, url: str) -> bool:
        """Atomically reserve a crawl slot for `url`. False => skip it."""
        async with self._claim_lock:
            if url in self.visited:
                return False
            if len(self.visited) >= self.max_pages:
                return False
            self.visited.add(url)
            return True

    async def _worker(self, worker_id: int, prompt: Optional[str] = None, schema: Optional[Any] = None):
        """
        A worker that picks URLs from the queue and processes them using a Tab.

        Runs until cancelled by `run()` (which happens once `queue.join()`
        reports every queued item has been accounted for). It deliberately does
        *not* bail out on an idle queue: a sibling worker may still be loading a
        page that is about to enqueue more links.
        """
        while True:
            current_url, depth = await self.queue.get()

            try:
                if depth > self.max_depth:
                    continue

                if not await self._claim(current_url):
                    continue

                logger.info(f"[Worker-{worker_id}] Crawling: {current_url} (Depth: {depth})")

                page = None
                try:
                    page = await self._browser.get(current_url, new_tab=True)
                    await page.sleep(self.page_settle_time)

                    final_url = self._normalize_url(page.url)
                    if final_url != current_url:
                        async with self._claim_lock:
                            self.visited.add(final_url)

                    # Extract Data
                    data = {}
                    if self.extraction_hook:
                        data = await self.extraction_hook(page)
                    else:
                        # Pass prompt/schema to extraction logic
                        data = await self._extract_content(page, prompt, schema)

                    await self._emit(data)

                    # Extract Links. Sitemap URLs arrive at depth 0, so links are
                    # explored from them too whenever max_depth allows it.
                    if depth < self.max_depth:
                        links = []
                        try:
                            # navigable=True keeps assets (.js/.css/images) out of
                            # the crawl frontier.
                            links = await page.get_all_urls(absolute=True, navigable=True)
                        except Exception as e:
                            logger.warning(f"[Worker-{worker_id}] CDP link extraction failed: {e}")

                        if not links:
                            logger.debug(f"[Worker-{worker_id}] Fallback to JS link extraction")
                            try:
                                js_links = await page.evaluate("""
                                    Array.from(document.querySelectorAll('a[href]')).map(a => a.href)
                                """)
                                if js_links and isinstance(js_links, list):
                                    links = js_links
                            except Exception as e:
                                logger.error(f"[Worker-{worker_id}] JS link extraction failed: {e}")

                        for link in links:
                            normalized_link = self._normalize_url(link)
                            if self._is_allowed(normalized_link) and normalized_link not in self.visited:
                                await self.queue.put((normalized_link, depth + 1))

                except Exception as e:
                    logger.error(f"[Worker-{worker_id}] Failed to process {current_url}: {e}")
                finally:
                    if page is not None:
                        try:
                            await page.close()
                        except Exception:
                            pass
            finally:
                self.queue.task_done()

    def _save_to_file(self, filename: str):
        """Saves results to a file based on extension."""
        if not self.results:
            logger.warning("No results to save.")
            return

        try:
            if filename.endswith(".json"):
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(self.results, f, indent=2, ensure_ascii=False)
            elif filename.endswith(".jsonl"):
                with open(filename, "w", encoding="utf-8") as f:
                    for item in self.results:
                        f.write(json.dumps(item, ensure_ascii=False) + "\n")
            elif filename.endswith(".csv"):
                # Preserve first-seen key order so the column layout is stable
                # across runs (a set gave a different order every time).
                all_keys = list(dict.fromkeys(k for d in self.results for k in d))
                with open(filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=all_keys)
                    writer.writeheader()
                    writer.writerows(self.results)
            elif filename.endswith(".md"):
                with open(filename, "w", encoding="utf-8") as f:
                    for item in self.results:
                        f.write(f"# {item.get('title', 'No Title')}\n")
                        f.write(f"Source: {item.get('url', 'Unknown URL')}\n\n")
                        f.write(item.get("markdown", ""))
                        f.write("\n\n---\n\n")
            else:
                logger.warning(f"Unknown file extension for {filename}. Saving as JSON.")
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(self.results, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(self.results)} results to {filename}")
        except Exception as e:
            logger.error(f"Failed to save results to {filename}: {e}")

    async def run(self, output_file: Optional[str] = None, prompt: Optional[str] = None, schema: Optional[Any] = None) -> List[Dict]:
        """
        Starts the crawling process.
        """
        # Initialize Browser
        from chuscraper.core.browser import Browser

        self._browser = await Browser.create(**self.browser_config)

        try:
            # Handle Sitemap Loading
            if self.sitemap_url:
                sitemap_urls = await self._fetch_sitemap(self.sitemap_url)
                logger.info(f"Found {len(sitemap_urls)} URLs from sitemap.")

                # Filter allowed domains just in case sitemap points externally
                for url in sitemap_urls:
                    if self._is_allowed(url):
                        await self.queue.put((self._normalize_url(url), 0))

            # Handle Start URLs (if any, though logic excludes both)
            elif self.start_urls:
                for url in self.start_urls:
                    await self.queue.put((self._normalize_url(url), 0))

            # Create workers (pass prompt/schema)
            workers = [asyncio.create_task(self._worker(i, prompt, schema)) for i in range(self.concurrency)]

            try:
                # Workers block on the queue forever, so join() is what signals
                # completion. Race it against the workers themselves so a worker
                # crashing can never leave us hanging on join() for good.
                drained = asyncio.create_task(self.queue.join())
                await asyncio.wait([drained, *workers], return_when=asyncio.FIRST_COMPLETED)
                if not drained.done():
                    logger.error("Crawl workers exited before the queue was drained.")
                    drained.cancel()
            finally:
                for w in workers:
                    w.cancel()
                await asyncio.gather(*workers, return_exceptions=True)

        finally:
            if self._browser:
                await self._browser.stop()

        if output_file and not self.on_page_crawled:
            self._save_to_file(output_file)
        elif output_file and self.on_page_crawled:
            logger.warning("File output is disabled when 'on_page_crawled' callback is provided. Handle saving in your callback.")

        return self.results
