import asyncio
import chuscraper as cs
import logging

logging.basicConfig(level=logging.DEBUG)

async def verify_fixes():
    # Use headless=True for the sandbox environment
    async with await cs.start(headless=True) as browser:
        print("--- 1. Testing goto() ---")
        tab = await browser.get("https://neurofiq.in")
        print(f"Page loaded: {tab.url}")

        print("\n--- 2. Testing scroll_down() ---")
        # This used to crash with AttributeError: 'str' object has no attribute 'to_json'
        try:
            await tab.scroll_down(10)
            print("scroll_down(10) successful!")
        except Exception as e:
            print(f"scroll_down(10) failed: {e}")
            import traceback
            traceback.print_exc()

        print("\n--- 3. Testing fill() resilience ---")
        # Find an input to test fill. Even if it doesn't re-render immediately,
        # we can verify the method still works.
        try:
            # Try to find any input
            inputs = await tab.query_selector_all("input")
            if inputs:
                target_input = inputs[0]
                print(f"Found input: {target_input.node_name}")
                await target_input.fill("test@example.com")
                print("fill() successful!")
            else:
                print("No input found to test fill()")
        except Exception as e:
            print(f"fill() failed: {e}")
            import traceback
            traceback.print_exc()

        print("\nVerification complete.")

if __name__ == "__main__":
    asyncio.run(verify_fixes())
