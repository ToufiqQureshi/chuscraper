import asyncio
import os
from pydantic import BaseModel
from chuscraper import start

# 1. Define what data you want using Pydantic
class HotelData(BaseModel):
    name: str
    price: str
    rating: str
    location: str
    amenities: list[str]

async def main():
    # Make sure you have GEMINI_API_KEY in environment
    # os.environ["GEMINI_API_KEY"] = "your_key_here"
    
    # 2. Start Chuscraper (Muscle)
    browser = await start(headless=False)
    page = await browser.get("https://www.makemytrip.com/hotels/hotel-details/?hotelId=201407231201556534")

    print("\n--- AI IS THINKING (ScrapeGraph style) ---")
    
    # 3. Use AI to extract (Brain)
    # No selectors needed! Just natural language.
    result = await page.ai_extract(
        prompt="Extract the hotel name, current price, rating, location, and a list of top 5 amenities.",
        schema=HotelData
    )

    print("\nEXTRACTED DATA:")
    print(f"Name: {result.name}")
    print(f"Price: {result.price}")
    print(f"Rating: {result.rating}")
    print(f"Location: {result.location}")
    print(f"Amenities: {', '.join(result.amenities)}")

    # 4. Ask a natural language question
    answer = await page.ai_ask("Is there a swimming pool in this hotel?")
    print(f"\nAI ANSWER: {answer}")

    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
