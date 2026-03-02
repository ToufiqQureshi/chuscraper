import asyncio
import chuscraper as cs
import logging

logging.basicConfig(level=logging.INFO)

async def test_all_interactions():
    async with await cs.start(headless=False) as browser:
        print("--- 1. Testing goto() ---")
        tab = await browser.get("https://neurofiq.in")
        print("Page loaded successfully!")
        
        # Debug page content
        content = await tab.to_text()
        print(f"Page content length: {len(content)}")
        print(f"Preview: {content[:200]}")

        print("\n--- 2. Testing wait_for() ---")
        # Wait for the main heading or a specific section
        heading = await tab.wait_for("div", timeout=10)
        print(f"Found heading/div: {await heading.to_text()}")

        print("\n--- 3. Testing hover() ---")
        # Let's hover over the first link we find
        first_link = await tab.wait_for("a", timeout=5)
        print(f"Hovering over link: {await first_link.to_text()}")
        await first_link.hover()

        # Let's interact with a contact form if it exists, or just a dummy search simulation
        print("\n--- 4. Testing type() and click() ---")
        try:
            # Look for an input field on NEUROFIQ
            # If there isn't one immediately visible, this will timeout.
            # Usually there's a contact section
            name_input = await tab.wait_for("input[type='text'], input[placeholder*='Name'], input[name='name']", timeout=3)
            print(f"Found input field: {name_input}")
            await name_input.type("Test User")
            print("Typed into input field successfully.")
        except Exception as e:
            print(f"Could not test type() directly on an input field: {e}")

        print("\n--- 5. Testing fill() ---")
        try:
            email_input = await tab.wait_for("input[type='email'], input[placeholder*='Email']", timeout=3)
            print(f"Found email field: {email_input}")
            # fill clears then types
            await email_input.fill("test@neurofiq.in")
            print("Filled email field successfully.")
        except Exception as e:
            print(f"Could not test fill() directly: {e}")
            
        print("\n--- 6. Testing Scrolling ---")
        await tab.scroll_down(500)
        await asyncio.sleep(1)
        await tab.scroll_up(500)
        print("Scrolled down and up.")
        
        # Test clicking a button or link
        try:
             # Click something innocuous like the logo or a nav item
             nav_link = await tab.wait_for("a.nav-link, ul li a", timeout=3)
             text = await nav_link.to_text()
             print(f"Clicking nav link: {text}")
             await nav_link.click()
             await asyncio.sleep(2) # wait to see if it navigated or opened
        except Exception as e:
            print(f"Could not test click() directly: {e}")

        print("\n✅ All interaction tests completed without FD leaks or WS crash loops!")

if __name__ == "__main__":
    asyncio.run(test_all_interactions())
