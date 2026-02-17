import asyncio
import os
import chuscraper as zd

async def robus_stealth_test():
    print("🛸 Starting ROBUS ULTIMATE STEALTH TEST (2026 Edition)...")
    
    # We use headless=True for the hardest test possible
    async with await zd.start(headless=True, stealth=True) as browser:
        page = browser.main_tab
        
        # 🧪 TEST 1: CreepJS (The Hardest)
        print("\n🧪 TEST 1: CreepJS (Total Fingerprinting)...")
        await page.goto("https://abrahamjuliot.github.io/creepjs/")
        await asyncio.sleep(10) # Heavy processing
        
        # Extract the fundamental 'Heady' markers or trust score if possible
        trust_score = await page.evaluate("() => document.querySelector('.trust-score')?.innerText")
        print(f"📊 CreepJS Trust Score: {trust_score or 'Unknown (Check manually)'}")

        # 🧪 TEST 2: Sannysoft (Automation Markers)
        print("\n🧪 TEST 2: Sannysoft (WebDriver & Chrome Object)...")
        await page.goto("https://bot.sannysoft.com/")
        await asyncio.sleep(5)
        
        # Check specific results
        results = await page.evaluate("""() => {
            const table = document.querySelector('table');
            return table ? table.innerText : "Not found";
        }""")
        print(f"📊 Sannysoft Highlights: {str(results)[:200]}...")

        # 🧪 TEST 3: PixelScan (Graphics & IP)
        print("\n🧪 TEST 3: PixelScan (Graphics/WebGPU Entropy)...")
        await page.goto("https://pixelscan.net/")
        await asyncio.sleep(5)
        
        # Extract detection result
        detection = await page.evaluate("() => document.querySelector('.detection-result')?.innerText")
        print(f"📊 PixelScan Result: {detection or 'Check manually (likely Green if no text)'}")

        print("\n✅ Robus Stealth Test Finished!")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(robus_stealth_test())
