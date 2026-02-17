import asyncio
import os
import chuscraper as zd

async def easy_syntax_demo():
    print("🚀 Running Easy Syntax Demo...")
    
    # 1. DIRECT START (No Config object needed!)
    # Parameters like 'stealth' and 'proxy' are now first-class citizens in start()
    async with await zd.start(headless=False, stealth=True) as browser:
        print("✅ Browser started with Zero Boilerplate.")
        
        # 2. BROWSER-LEVEL SHORTCUT
        # No need to access main_tab explicitly for simple navigations
        print("📍 Navigating via browser.goto()...")
        await browser.goto("https://google.com")
        
        # 3. INTUITIVE ALIASES
        # 'goto' matches Playwright/Puppeteer naming
        print("🔗 Checking 'goto' alias on tab...")
        page = browser.main_tab
        await page.goto("https://example.com")
        
        # 4. ONE-LINER EXTRACTION
        # 'title()' is now a direct async method
        # 'select_text()' gets text in one go
        title = await page.title()
        header = await page.select_text("h1")
        
        print(f"📄 Page Title: {title}")
        print(f"📄 Header Text: {header}")
        
        # 5. SCRAPE SHORTCUT
        # browser.scrape() quickly finds an element on the main tab
        h1_el = await browser.scrape("h1")
        if h1_el:
            print(f"✅ 'browser.scrape()' confirmed: {h1_el.text}")

        print("🎉 Demo finished successfully!")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(easy_syntax_demo())
