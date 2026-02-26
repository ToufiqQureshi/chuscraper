import asyncio
import logging
import json
import csv
from typing import List, Dict, Optional, Set, Callable, Any, Literal, Awaitable
from urllib.parse import urlparse, urljoin, urldefrag
from chuscraper.core.tab import Tab
from chuscraper.core.browser import Browser

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
    """

    def __init__(
        self,
        start_urls: List[str] | str | None = None,
        sitemap_url: str | None = None,
        max_pages: int = 10,
        max_depth: int = 2,
        concurrency: int = 2,
        formats: List[FormatType] = ["markdown"],
        browser_config: Optional[Dict] = None,
        extraction_hook: Optional[Callable[[Tab], Dict]] = None,
        on_page_crawled: Optional[Callable[[Dict], Awaitable[None]]] = None,
        map_only: bool = False
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
        self.formats = formats
        self.browser_config = browser_config or {}
        self.extraction_hook = extraction_hook
        self.on_page_crawled = on_page_crawled
        self.map_only = map_only

        self.visited: Set[str] = set()
        self.queue: asyncio.Queue = asyncio.Queue()
        self.results: List[Dict] = []
        self._browser: Optional[Browser] = None

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

    async def _fetch_sitemap(self, url: str) -> List[str]:
        """Fetches and parses a sitemap (and nested sitemaps)."""
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
                        nested_urls = await self._fetch_sitemap(loc.text.strip())
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

    async def _extract_content(self, page: Tab) -> Dict[str, Any]:
        """Extracts content based on configured formats."""
        try:
            title = await page.evaluate("document.title")
        except:
            title = "No Title"

        data = {
            "url": self._normalize_url(page.url),
            "title": title,
        }

        if "markdown" in self.formats:
            data["markdown"] = await page.markdown()

        if "html" in self.formats:
            data["html"] = await page.get_content()

        if "text" in self.formats:
            try:
                data["text"] = await page.to_text()
            except AttributeError:
                 data["text"] = await page.evaluate("document.body.innerText")

        return data

    async def _worker(self, worker_id: int):
        """
        A worker that picks URLs from the queue and processes them using a Tab.
        """
        while True:
            if len(self.visited) >= self.max_pages:
                try:
                    self.queue.get_nowait()
                    self.queue.task_done()
                except asyncio.QueueEmpty:
                    pass
                await asyncio.sleep(0.1)
                continue

            try:
                queue_item = await asyncio.wait_for(self.queue.get(), timeout=2.0)
                current_url, depth = queue_item
            except (asyncio.TimeoutError, asyncio.QueueEmpty):
                if len(self.visited) > 0 and len(self.visited) < self.max_pages:
                     # Debug log reduced to avoid spam
                     pass
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
                page = await self._browser.get(current_url, new_tab=True)
                await page.sleep(4)

                final_url = self._normalize_url(page.url)
                if final_url != current_url:
                     self.visited.add(final_url)

                # Extract Data
                data = {}
                if self.map_only:
                    data = {"url": final_url}
                elif self.extraction_hook:
                    data = await self.extraction_hook(page)
                else:
                    data = await self._extract_content(page)

                # Store or Stream
                if self.on_page_crawled:
                    try:
                        if asyncio.iscoroutinefunction(self.on_page_crawled):
                            await self.on_page_crawled(data)
                        else:
                            pass
                    except Exception as e:
                        logger.error(f"Error in on_page_crawled callback: {e}")
                else:
                    self.results.append(data)

                # Extract Links (Only if NOT using sitemap mode, OR if depth allows exploration from sitemap URLs)
                # Actually, Firecrawl usually treats sitemap URLs as depth 0.
                # But here we treat them as whatever depth they came in (0).
                # If max_depth > 0, we should explore links from sitemap pages too.
                if depth < self.max_depth:
                    links = []
                    try:
                        links = await page.get_all_urls(absolute=True)
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
                        if self._is_allowed(normalized_link):
                            if normalized_link not in self.visited:
                                await self.queue.put((normalized_link, depth + 1))

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
                all_keys = set().union(*(d.keys() for d in self.results))
                with open(filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=list(all_keys))
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

            # Create workers
            workers = [asyncio.create_task(self._worker(i)) for i in range(self.concurrency)]

            await self.queue.join()

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
