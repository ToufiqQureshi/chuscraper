"""
Lead scraper for extracting contact information from web pages.

Combines:
- Browser automation (chuscraper)
- Human-like behavior
- Rate limiting
- Contact extraction
"""

import asyncio
from datetime import datetime
from typing import Dict, Optional, List
from ..core.behavior import HumanBehavior
from ..core.limiter import RateLimiter
from ..extractors.contact import ContactExtractor


class LeadScraper:
    """Scrape lead information from web pages with anti-detection."""
    
    def __init__(
        self,
        rate_limit_requests: int = 10,
        rate_limit_window: int = 60,
        human_behavior: bool = True,
        stealth_mode: bool = True
    ):
        """
        Initialize lead scraper.
        
        Args:
            rate_limit_requests: Max requests per window
            rate_limit_window: Time window in seconds
            human_behavior: Enable human-like behavior
            stealth_mode: Enable stealth mode
        """
        self.rate_limiter = RateLimiter(
            max_requests=rate_limit_requests,
            time_window=rate_limit_window
        )
        self.behavior = HumanBehavior()
        self.human_behavior_enabled = human_behavior
        self.stealth_mode = stealth_mode
    
    async def scrape_page(
        self,
        url: str,
        browser=None,
        extract_config: Optional[Dict] = None
    ) -> Dict:
        """
        Scrape leads from a single page.
        
        Args:
            url: URL to scrape
            browser: Existing browser instance (optional)
            extract_config: Configuration for extraction
            
        Returns:
            Dict with lead data
        """
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Import here to avoid circular import
        import chuscraper as cs
        
        # Start browser if not provided
        close_browser = False
        if not browser:
            browser = await cs.start(stealth=self.stealth_mode)
            close_browser = True
        
        try:
            # Navigate to page
            page = await browser.get(url)
            
            # Human-like behavior
            if self.human_behavior_enabled:
                await self.behavior.random_delay(2, 4)
                await self.behavior.scroll_naturally(page, direction='to_bottom', speed='medium')
                await self.behavior.mouse_movement_pattern(page, num_moves=3)
            
            # Extract HTML content
            html = await page.get_content()
            
            # Extract contacts
            extract_config = extract_config or {}
            contacts = ContactExtractor.extract_all(
                html,
                extract_emails=extract_config.get('emails', True),
                extract_phones=extract_config.get('phones', True),
                extract_social=extract_config.get('social', True),
                phone_countries=extract_config.get('phone_countries', ['IN', 'US', 'UK'])
            )
            
            # Build result
            result = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'data': contacts,
                'success': True,
                'error': None
            }
            
            return result
        
        except Exception as e:
            return {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'data': None,
                'success': False,
                'error': str(e)
            }
        
        finally:
            if close_browser:
                await browser.stop()
    
    async def scrape_multiple(
        self,
        urls: List[str],
        max_concurrent: int = 3,
        extract_config: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Scrape multiple URLs concurrently.
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent scrapes
            extract_config: Extraction configuration
            
        Returns:
            List of scrape results
        """
        import chuscraper as cs
        from ..core.limiter import ConcurrencyLimiter
        
        # Start browser once for all scrapes
        browser = await cs.start(stealth=self.stealth_mode)
        concurrency_limiter = ConcurrencyLimiter(max_concurrent=max_concurrent)
        
        async def scrape_with_limit(url):
            async with concurrency_limiter:
                return await self.scrape_page(url, browser=browser, extract_config=extract_config)
        
        try:
            # Scrape all URLs
            tasks = [scrape_with_limit(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        'url': urls[i],
                        'scraped_at': datetime.now().isoformat(),
                        'data': None,
                        'success': False,
                        'error': str(result)
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
        
        finally:
            await browser.stop()
    
    def get_stats(self, results: List[Dict]) -> Dict:
        """
        Get statistics from scrape results.
        
        Args:
            results: List of scrape results
            
        Returns:
            Statistics dict
        """
        total = len(results)
        successful = sum(1 for r in results if r['success'])
        failed = total - successful
        
        # Count total leads
        total_emails = 0
        total_phones = 0
        total_social = 0
        
        for result in results:
            if result['success'] and result['data']:
                total_emails += len(result['data'].get('emails', []))
                total_phones += len(result['data'].get('phones', []))
                social = result['data'].get('social', {})
                for links in social.values():
                    total_social += len(links)
        
        return {
            'total_pages': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'total_emails_found': total_emails,
            'total_phones_found': total_phones,
            'total_social_links': total_social
        }
