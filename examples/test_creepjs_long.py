import asyncio
import os
import chuscraper as zd

async def run_long_audit():
    # Ensure assets directory exists
    proof_dir = os.path.abspath("docs/assets/proof")
    os.makedirs(proof_dir, exist_ok=True)
    
    # Configure stealth browser with residential proxy
    # Using the optimized config that passed IPHey
    proxy_url = "http://11de131690b3fdc7ba16__cr.in:e3e7d1a8f82bd8e3@gw.dataimpulse.com:823"
    config = zd.Config(
        browser="chrome", 
        headless=False,
        stealth=True,
        disable_webgl=True, # Disable WebGL to prevent hardware fingerprint leaks
        proxy=proxy_url,
        # Explicitly set a common Windows User-Agent to match the platform
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        browser_args=[
            "--window-size=1920,1080",
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
        ]
    )
    
    # Target only CreepJS with a 5-minute wait
    site = {"name": "creepjs_long", "url": "https://abrahamjuliot.github.io/creepjs/", "wait": 300}
    
    print(f"Starting 5-minute stress test for {site['name']}...")
    print("This will take a while. Please be patient.")
    
    async with await zd.start(config) as browser:
        try:
            page = await browser.get(site['url'])
            
            print(f"Page loaded. Waiting for {site['wait']} seconds...")
            # Wait for results to load and stabilize
            await asyncio.sleep(site['wait'])
            
            # Take screenshot using the correct method
            screenshot_path = os.path.join(proof_dir, f"{site['name']}_proof.png")
            await page.save_screenshot(screenshot_path, format="png")
            print(f"Captured proof for {site['name']} at {screenshot_path}")
            
        except Exception as e:
            print(f"Error auditing {site['name']}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_long_audit())
