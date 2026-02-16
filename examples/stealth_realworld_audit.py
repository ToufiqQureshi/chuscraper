import asyncio
import os
import chuscraper as zd

async def run_realworld_audit():
    # Ensure assets directory exists
    proof_dir = os.path.abspath("docs/assets/proof")
    os.makedirs(proof_dir, exist_ok=True)
    
    # Configure stealth browser with residential proxy
    # Using the optimized config that passed IPHey (Native Chrome + Headful)
    proxy_url = "http://11de131690b3fdc7ba16__cr.in:e3e7d1a8f82bd8e3@gw.dataimpulse.com:823"
    config = zd.Config(
        browser="chrome", 
        headless=False,
        stealth=True,
        disable_webgl=True, 
        proxy=proxy_url,
        # Explicitly set a common Windows User-Agent
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        browser_args=[
            "--window-size=1920,1080",
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
        ]
    )
    
    # Real-world targets
    sites = [
        # Cloudflare Turnstile Demo
        {"name": "cloudflare_turnstile", "url": "https://turnstile-demo.employee-account-d41.workers.dev/", "wait": 10},
        
        # DataDome (Research Page)
        {"name": "datadome_research", "url": "https://antoinevastel.com/bots/datadome", "wait": 10},
        
        # Akamai (Nike - Known Akamai Bot Manager user)
        {"name": "akamai_nike", "url": "https://www.nike.com/", "wait": 15},
    ]
    
    async with await zd.start(config) as browser:
        for site in sites:
            print(f"Auditing {site['name']}...")
            try:
                page = await browser.get(site['url'])
                
                # Wait for potential challenges to resolve or page to load
                await asyncio.sleep(site['wait'])
                
                # Take screenshot
                screenshot_path = os.path.join(proof_dir, f"{site['name']}_proof.png")
                await page.save_screenshot(screenshot_path, format="png")
                print(f"Captured proof for {site['name']} at {screenshot_path}")
                
            except Exception as e:
                print(f"Error auditing {site['name']}: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_realworld_audit())
