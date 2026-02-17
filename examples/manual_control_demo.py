import asyncio
import os
import chuscraper as zd
from chuscraper import cdp

async def manual_demo():
    print("🚀 Starting manual control demo...")
    
    # Config: Headless=False so you can see it
    config = zd.Config(
        browser="chrome",
        headless=False,
        stealth=True
    )
    
    # Use 'async with' to ensure cleanup, but we do everything manually inside
    async with await zd.start(config) as browser:
        print("✅ Browser started.")
        
        # User has full control over the 'main_tab'
        # No extra tabs will be created unless YOU call them
        page = browser.main_tab
        
        # Step 1: Manual Navigation
        print("📍 Navigating to example.com...")
        await page.get("https://example.com")
        
        # Step 2: Explicit Wait
        print("⏳ Waiting for 3 seconds...")
        await asyncio.sleep(3)
        
        # Step 3: Manual Element Selection
        print("🔍 Extracting H1 text...")
        h1 = await page.select("h1")
        if h1:
            print(f"📄 Found Header: {h1.text}")
        
        # Step 4: Custom JS Execution
        print("⚡ Changing background color via JS...")
        await page.evaluate("document.body.style.backgroundColor = 'lightblue'")
        await asyncio.sleep(2)
        
        # Step 5: Manual Target Info Check
        print(f"ℹ️  Current Tab Info: Title='{page.title}', URL='{page.url}'")
        
        print("🏁 Demo complete. Browser will close now.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(manual_demo())
