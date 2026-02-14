import asyncio
import sys
import os

async def check_health():
    print("--- CHUSCRAPER DEEP HEALTH CHECK ---")
    
    # 1. Version Check
    try:
        from chuscraper import __version__
        print(f"[OK] Chuscraper Version: {__version__}")
    except Exception as e:
        print(f"[FAIL] Could not import version: {e}")

    # 2. Core Import Check
    try:
        from chuscraper import start, Browser, Tab
        print("[OK] Core components imported successfully.")
    except Exception as e:
        print(f"[FAIL] Core import failed: {e}")

    # 3. AI Module & Optional Dependency Check
    print("\n--- AI MODULE STATUS ---")
    try:
        from chuscraper import ai
        print("[OK] AI module structure found.")
        
        # Test lazy-loading of bs4
        try:
            from bs4 import BeautifulSoup
            print("[INFO] beautifulsoup4 is installed.")
        except ImportError:
            print("[INFO] beautifulsoup4 is NOT installed (Optional).")

        # Test providers
        try:
            import google.genai
            print("[INFO] google-genai is installed.")
        except ImportError:
            print("[INFO] google-genai is NOT installed (Optional).")
            
    except Exception as e:
        print(f"[FAIL] AI module import error: {e}")

    # 4. Functional Test (Basic Browser Start + Navigation)
    print("\n--- FUNCTIONAL TEST (CORE) ---")
    try:
        from chuscraper import start
        browser = await start(headless=True)
        page = await browser.get("https://api.ipify.org?format=json")
        content = await page.evaluate("document.body.innerText")
        print(f"[OK] Browser started and navigated to: {content}")
        await browser.stop()
    except Exception as e:
        print(f"[FAIL] Functional core test failed: {e}")

    print("\n--- HEALTH CHECK COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(check_health())
