import asyncio
import os
import chuscraper as cs

async def stealth_check_2026():
    print("🕵️‍♂️ Running Chuscraper Next-Gen Stealth Check...")
    
    # Start with stealth enabled
    async with await cs.start(headless=False, stealth=True) as browser:
        page = browser.main_tab
        
        # 1. Check WebGPU Presence (Spoofed)
        gpu_detected = await page.evaluate("() => !!navigator.gpu")
        print(f"✅ WebGPU Detected: {gpu_detected}")
        
        # 2. Check navigator.webdriver (Should be undefined)
        webdriver = await page.evaluate("() => navigator.webdriver")
        print(f"✅ navigator.webdriver: {webdriver} (Expected: undefined)")
        
        # 3. Check Hardware alignment
        cores = await page.evaluate("() => navigator.hardwareConcurrency")
        memory = await page.evaluate("() => navigator.deviceMemory")
        print(f"✅ Hardware reported: {cores} Cores, {memory}GB Memory")

        # 4. Visit detection sites for manual visual proof if needed
        # In a real environment, we'd take screenshots
        print("🌍 Visiting CreepJS for entropy check...")
        await page.goto("https://abrahamjuliot.github.io/creepjs/")
        await asyncio.sleep(5)
        
        print("🌍 Visiting BrowserLeaks (WebGL/Audio)...")
        await page.goto("https://browserleaks.com/webgl")
        await asyncio.sleep(3)
        await page.goto("https://browserleaks.com/audio")
        await asyncio.sleep(3)

        print("🎉 Stealth verification script finished!")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(stealth_check_2026())
