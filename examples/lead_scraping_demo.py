"""
Lead Scraping Demo - Complete Example

This demo shows how to use chuscraper for lead scraping:
1. Scrape a single page
2. Scrape multiple pages
3. Crawl entire domain
4. Export to CSV/JSON

Make sure you have chuscraper installed:
    pip install chuscraper
"""

import asyncio
from chuscraper.leads import LeadScraper, DomainCrawler, LeadExporter


async def demo_single_page():
    """Demo: Scrape a single page for leads."""
    print("\\n=== Single Page Scraping ===\\n")
    
    # Initialize scraper
    scraper = LeadScraper(
        rate_limit_requests=10,
        rate_limit_window=60,
        human_behavior=True
    )
    
    # Scrape a page
    result = await scraper.scrape_page("https://example.com/contact")
    
    print(f"URL: {result['url']}")
    print(f"Success: {result['success']}")
    
    if result['success']:
        data = result['data']
        print(f"Emails found: {len(data['emails'])}")
        print(f"Phones found: {len(data['phones'])}")
        print(f"Social links: {sum(len(links) for links in data['social'].values())}")
        
        # Print emails
        if data['emails']:
            print(f"\\nEmails: {', '.join(data['emails'][:3])}")


async def demo_multiple_pages():
    """Demo: Scrape multiple pages concurrently."""
    print("\\n=== Multiple Pages Scraping ===\\n")
    
    scraper = LeadScraper()
    
    # List of URLs to scrape
    urls = [
        "https://example.com/contact",
        "https://example.com/about",
        "https://example.com/team"
    ]
    
    # Scrape all pages
    results = await scraper.scrape_multiple(
        urls,
        max_concurrent=3
    )
    
    # Get stats
    stats = scraper.get_stats(results)
    print(f"Total pages: {stats['total_pages']}")
    print(f"Successful: {stats['successful']}")
    print(f"Total emails: {stats['total_emails_found']}")
    print(f"Total phones: {stats['total_phones_found']}")
    
    return results


async def demo_domain_crawl():
    """Demo: Crawl entire domain for leads."""
    print("\\n=== Domain Crawling ===\\n")
    
    crawler = DomainCrawler(
        max_pages=20,
        max_concurrent=3,
        rate_limit_requests=10
    )
    
    # Crawl domain
    results = await crawler.crawl("https://example.com")
    
    print(f"Pages crawled: {len(results)}")
    
    # Count total leads
    total_emails = sum(
        len(r['data']['emails']) 
        for r in results 
        if r['success'] and r['data']
    )
    print(f"Total unique emails: {total_emails}")
    
    return results


async def demo_export():
    """Demo: Export leads to CSV and JSON."""
    print("\\n=== Exporting Leads ===\\n")
    
    # Scrape some pages
    scraper = LeadScraper()
    results = await scraper.scrape_multiple([
        "https://example.com/contact",
        "https://example.com/about"
    ])
    
    # Deduplicate
    results = LeadExporter.deduplicate_emails(results)
    
    # Export to CSV
    LeadExporter.to_csv(results, "leads.csv")
    print("✅ Exported to leads.csv")
    
    # Export to JSON
    LeadExporter.to_json(results, "leads.json", pretty=True)
    print("✅ Exported to leads.json")
    
    # Filter by criteria
    filtered = LeadExporter.filter_by_criteria(
        results,
        min_emails=1  # Only pages with at least 1 email
    )
    print(f"\\nFiltered results: {len(filtered)} pages with emails")


async def demo_custom_config():
    """Demo: Custom extraction configuration."""
    print("\\n=== Custom Configuration ===\\n")
    
    scraper = LeadScraper(human_behavior=True)
    
    # Custom extraction config
    extract_config = {
        'emails': True,
        'phones': True,
        'social': True,
        'phone_countries': ['IN', 'US']  # Only India and US numbers
    }
    
    result = await scraper.scrape_page(
        "https://example.com/contact",
        extract_config=extract_config
    )
    
    print(f"Config used: India and US phone formats only")
    print(f"Phones found: {result['data']['phones']}")


async def main():
    """Run all demos."""
    print("=" * 60)
    print("  CHUSCRAPER - Lead Scraping Demo")
    print("=" * 60)
    
    # Run demos
    await demo_single_page()
    
    results = await demo_multiple_pages()
    
    await demo_domain_crawl()
    
    await demo_export()
    
    await demo_custom_config()
    
    print("\\n" + "=" * 60)
    print("  Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    # Run async demos
    asyncio.run(main())
