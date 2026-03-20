import asyncio
from chuscraper.mobile import MobileDevice
from bs4 import BeautifulSoup
import re

async def scrape_agoda():
    try:
        device = await MobileDevice().connect()
        print(f"[SUCCESS] Connected to Android: {device.serial}")
        
        # 1. Look for the search button by Text since Resource IDs are obfuscated (Compose)
        print("\n--- 1. Initiating Search ---")
        
        # The search button might be an android.widget.Button that is a sibling of the TextView "Search"
        # Since find_element by text matches the TextView, not the Button itself, 
        # we can just tap the center of the "Search" TextView label bounded box.
        soup = await device.dump_hierarchy()
        search_text_node = soup.find(attrs={"text": "Search"})
        
        if search_text_node:
            bounds = search_text_node.get("bounds") # e.g., "[549,1286][699,1351]"
            if bounds:
                # Parse bounds coordinates to click the center
                coords = re.findall(r'\d+', bounds)
                if len(coords) == 4:
                    x1, y1, x2, y2 = map(int, coords)
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    
                    print(f"Executing Tap on 'Search' button at coordinates: ({center_x}, {center_y})")
                    await device.tap(center_x, center_y)
                    print("[SUCCESS] Clicked Search!")
        else:
            print("[ERROR] Search generic text not found.")
            return

        # 2. Wait 4 seconds for hotels to load
        print("\n--- 2. Waiting 4 seconds for results to load ---")
        await asyncio.sleep(4)

        # 3. Dump hierarchy again to find the first hotel
        print("\n--- 3. Clicking First Hotel Result ---")
        soup_results = await device.dump_hierarchy()
        
        # Find the first prominent TextView that looks like a Hotel Title 
        # (usually a long text in a clickable container or large bounds)
        hotel_titles = soup_results.find_all("node", attrs={"class": "android.widget.TextView"})
        
        clicked = False
        for title in hotel_titles:
            text = title.get("text", "")
            # Skip common UI text that isn't a hotel name
            if text and text not in ["Search", "Sort", "Filter", "Map", "AED", "Overnight"]:
                bounds = title.get("bounds")
                if bounds:
                    coords = re.findall(r'\d+', bounds)
                    if len(coords) == 4:
                        x1, y1, x2, y2 = map(int, coords)
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        
                        print(f"Executing Tap on likely first hotel '{text}' at coordinates: ({center_x}, {center_y})")
                        await device.tap(center_x, center_y)
                        print("[SUCCESS] Clicked first hotel result!")
                        clicked = True
                        break
        
        if not clicked:
            print("[ERROR] Could not automatically click a hotel from the results layout.")

    except Exception as e:
        print(f"[ERROR] Script crashed: {e}")

if __name__ == "__main__":
    asyncio.run(scrape_agoda())
