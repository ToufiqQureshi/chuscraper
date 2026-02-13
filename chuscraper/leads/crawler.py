"""
Domain crawler for scraping multiple pages within same domain.

Features:
- Multi-threaded crawling
- Same-domain link discovery
- Max page limit
- Progress tracking
"""

import asyncio
from typing import Set, List, Dict, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from .scraper import LeadScraper
from ..core.limiter import ConcurrencyLimiter


class DomainCrawler:
    """Crawl and scrape entire domain for leads."""
    
    def __init__(
        self,
        max_pages: int = 50,
        max_concurrent: int = 3,
        rate_limit_requests: int = 10,
        same_domain_only: bool = True
    ):
        """
        Initialize domain crawler.
        
        Args:
            max_pages: Maximum pages to crawl
            max_concurrent: Maximum concurrent requests
            rate_limit_requests: Rate limit for requests
            same_domain_only: Only crawl same domain
        """
        self.max_pages = max_pages
        self.max_concurrent = max_concurrent
        self.same_domain_only = same_domain_only
        self.scraper = LeadScraper(rate_limit_requests=rate_limit_requests)
        self.visited: Set[str] = set()
        self.to_visit: List[str] = []
    
    async def crawl(
        self,
        start_url: str,
        extract_config: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Crawl domain starting from URL.
        
        Args:
            start_url: Starting URL
            extract_config: Extraction configuration
            
        Returns:
            List of scrape results
        """
        import chuscraper as cs
        
        # Initialize
        self.visited.clear()
        self.to_visit = [start_url]
        results = []
        
        # Get base domain
        base_domain = self._get_domain(start_url)
        
        # Start browser
        browser = await cs.start(stealth=True)
        concurrency_limiter = ConcurrencyLimiter(max_concurrent=self.max_concurrent)
        
        try:
            while self.to_visit and len(self.visited) < self.max_pages:
                # Get next batch of URLs
                batch_size = min(self.max_concurrent, len(self.to_visit))
                current_batch = self.to_visit[:batch_size]
                self.to_visit = self.to_visit[batch_size:]
                
                # Crawl batch
                tasks = []
                for url in current_batch:
                    if url not in self.visited:
                        self.visited.add(url)
                        tasks.append(self._scrape_and_discover(
                            url, browser, base_domain, concurrency_limiter, extract_config
                        ))
                
                # Wait for batch
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        continue
                    
                    scrape_result, new_urls = result
                    results.append(scrape_result)
                    
                    # Add new URLs to queue
                    for new_url in new_urls:
                        if new_url not in self.visited and new_url not in self.to_visit:
                            if len(self.visited) + len(self.to_visit) < self.max_pages:
                                self.to_visit.append(new_url)
        
        finally:
            await browser.stop()
        
        return results
    
    async def _scrape_and_discover(
        self,
        url: str,
        browser,
        base_domain: str,
        concurrency_limiter,
        extract_config: Optional[Dict]
    ):
        """Scrape page and discover new links."""
        async with concurrency_limiter:
            # Scrape page
            scrape_result = await self.scraper.scrape_page(
                url, browser=browser, extract_config=extract_config
            )
            
            # Discover links
            new_urls = []
            if scrape_result.get('success'):
                try:
                    page = await browser.get(url)
                    html = await page.get_content()
                    new_urls = self._extract_links(html, url, base_domain)
                except:
                    pass
            
            return scrape_result, new_urls
    
    def _extract_links(self, html: str, current_url: str, base_domain: str) -> List[str]:
        """Extract links from HTML."""
        links = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            for anchor in soup.find_all('a', href=True):
                href = anchor['href']
                
                # Convert to absolute URL
                absolute_url = urljoin(current_url, href)
                
                # Clean URL (remove fragments)
                absolute_url = absolute_url.split('#')[0]
                
                # Check same domain
                if self.same_domain_only:
                    if self._get_domain(absolute_url) != base_domain:
                        continue
                
                # Check if valid HTTP(S)
                if absolute_url.startswith(('http://', 'https://')):
                    links.append(absolute_url)
        
        except:
            pass
        
        return links
    
    @staticmethod
    def _get_domain(url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc
    
    def get_progress(self) -> Dict:
        """Get current crawl progress."""
        return {
            'visited': len(self.visited),
            'queued': len(self.to_visit),
            'total': len(self.visited) + len(self.to_visit),
            'max_pages': self.max_pages
        }
