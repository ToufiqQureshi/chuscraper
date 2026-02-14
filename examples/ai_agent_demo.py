import asyncio
import os
from pydantic import BaseModel
from chuscraper import start

# 1. Structured Schema
class SearchResults(BaseModel):
    hotel_names: list[str]
    lowest_price: str

async def main():
    # Make sure you have GEMINI_API_KEY in environment
    # os.environ["GEMINI_API_KEY"] = "your_key"
    
    # 2. Start Chuscraper
    browser = await start(headless=False)
    page = await browser.get("https://www.makemytrip.com/")

    print("\n--- AI PILOT: SEARCHING AUTONOMOUSLY ---")
    # 3. Autonomous Navigation (AI Pilot)
    # The agent will find the search fields, type the destination, and click search.
    # Note: MMT home can be complex, so we give it a clear goal.
    success = await page.ai_pilot("Search for hotels in Goa for next week.")
    
    if success:
        print("\n--- AI VISION: EXTRACTING FROM VIEWPORT ---")
        # 4. Vision Extraction
        # Useful if the results page has complex dynamic elements.
        results = await page.ai_visual_extract(
            prompt="Extract the names of the first 3 hotels and the lowest price you see.",
            schema=SearchResults
        )
        print(f"Extracted: {results}")

        # 5. Self-Healing Selector
        # AI learns a selector that you can use in code later without LLM cost.
        selector = await page.ai_learn_selector("The hotel name of the first result")
        print(f"\nLEARNED SELECTOR: {selector}")
    else:
        print("Pilot failed to reach the results page.")

    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
