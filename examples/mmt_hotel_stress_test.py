import asyncio
import os
import random
import chuscraper as zd

async def run_mmt_test():
    # 1. URLs
    home_url = "https://www.makemytrip.com/"
    target_url = "https://www.makemytrip.com/hotels/hotel-listing/?checkin=02162026&checkout=02172026&locusId=CTJAI&locusType=city&city=CTJAI&country=IN&searchText=Cygnett%20Style%20Ganga%20Hotel&roomStayQualifier=1e0e&_uCurrency=INR&reference=hotel&rf=directSearch&lat=26.814932&lng=75.86291&topHtlId=202311282002508888&type=hotel&rsc=1e1e0e"
    
    # 2. Proxy Configuration (Residential)
    proxy_url = "http://11de131690b3fdc7ba16__cr.in:e3e7d1a8f82bd8e3@gw.dataimpulse.com:823"

    print(f"🚀 Starting ENHANCED MMT Stealth Test (Fixed API)...")
    print(f"🛡️  Banner-fix active: AutomationControlled flag removed.")

    config = zd.Config(
        browser="chrome",
        headless=False,
        stealth=True,
        proxy=proxy_url
    )

    async with await zd.start(config) as browser:
        for i in range(1, 11):
            print(f"\n🔄 Iteration #{i} of 10...")
            try:
                # --- STEP A: Visit Home Page First ---
                print("🏠 Visiting Home Page...")
                page = await browser.get(home_url)
                
                print("🖱️  Simulating human scrolling and movement...")
                await asyncio.sleep(random.uniform(2, 4))
                
                # Use native scroll_down method
                await page.scroll_down(amount=random.randint(20, 50))
                await asyncio.sleep( random.uniform(1, 2) )
                
                # Custom JS for mouse jitter (simulates activity)
                await page.evaluate("""
                    const jitter = () => {
                        const event = new MouseEvent('mousemove', {
                            view: window, bubbles: true, cancelable: true,
                            clientX: Math.random() * window.innerWidth,
                            clientY: Math.random() * window.innerHeight
                        });
                        document.dispatchEvent(event);
                    };
                    for(let j=0; j<5; j++) setTimeout(jitter, j*200);
                """)
                
                await asyncio.sleep(random.uniform(2, 4))
                
                # --- STEP B: Navigate to Listing ---
                print(f"🔗 Navigating to Hotel Listing...")
                await page.get(target_url)
                
                # Wait for MMT to finish loading
                print("⏳ Waiting for content load...")
                await asyncio.sleep(random.uniform(8, 12)) 
                
                content = await page.get_content()
                if "Access Denied" in content or "Shield" in content:
                    print(f"❌ Blocked by Akamai on iteration {i}")
                    await page.save_screenshot(f"mmt_block_iter_{i}.png")
                else:
                    if "Cygnett" in content:
                        print(f"✅ SUCCESS: Hotel listing visible!")
                    elif "200-OK" in content and len(content) < 500:
                        print("⚠️ Black screen (200-OK) detected. Still partially blocked or script load failed.")
                        await page.save_screenshot(f"mmt_black_screen_{i}.png")
                    else:
                        print(f"✅ Loaded but Cygnett not found. Page length: {len(content)}")
                        await page.save_screenshot(f"mmt_unknown_load_{i}.png")

                # Random sleep
                await asyncio.sleep(random.uniform(5, 10))

            except Exception as e:
                print(f"⚠️ Error: {e}")
                continue

    print("\n✨ Test Finished.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_mmt_test())
