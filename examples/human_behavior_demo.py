import asyncio
import os
import chuscraper as zd

async def human_behavior_demo():
    print("🤖 Starting Behavioral Humanization Demo...")
    
    # Headless=False to see the mouse moving!
    async with await zd.start(headless=False, stealth=True) as browser:
        page = browser.main_tab
        
        # Using a more reliable test site
        url = "https://the-internet.herokuapp.com/login"
        print(f"📍 Navigating to {url}...")
        await page.goto(url)
        
        # 1. Human Type (Username)
        print("⌨️  Human Typing: 'tomsmith'...")
        await page.human_type("#username", "tomsmith")
        
        # 2. Human Type (Password)
        print("⌨️  Human Typing: 'SuperSecretPassword!'...")
        await page.human_type("#password", "SuperSecretPassword!")
        
        # 3. Human Click (Login Button)
        print("🖱️  Human Clicking: 'Login' button...")
        # The button is <button class="radius" type="submit">
        await page.human_click("button[type='submit']")
        
        print("⏳ Waiting for result...")
        await asyncio.sleep(5)
        
        if await page.find_elements_by_text("You logged into a secure area!"):
             print("✅ Login SUCCESS! The bot acted like a human.")
        else:
             print("❌ Login check failed (or different text).")

        print("✅ Demo interaction complete!")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(human_behavior_demo())
