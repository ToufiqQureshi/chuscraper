import asyncio
from chuscraper.mobile import MobileDevice

async def automate_agoda_booking_flow():
    print("--- 1. Connecting to Android Device ---")
    try:
        device = await MobileDevice().connect()
        print(f"[SUCCESS] Connected to device: {device.serial}\n")
        
        # Step 1: Click the main "Search" button
        print("--- 2. Initiating Search ---")
        search_btn = await device.find_element(text="Search")
        if search_btn:
            await search_btn.click()
            print("[SUCCESS] Clicked 'Search' button")
        else:
            print("[ERROR] Could not find 'Search' button. Make sure you are on the Home screen.")
            return
            
        # Step 2: Wait for search results
        print("\n⏳ Waiting 10 seconds for search results to load...")
        await asyncio.sleep(10)
        
        # Step 3: Click the Target Hotel (Aavri Hotel Deira, Dubai)
        print("\n--- 3. Selecting Hotel ---")
        hotel_listing = await device.find_element(text="Aavri Hotel Deira, Dubai")
        if hotel_listing:
            await hotel_listing.click()
            print("[SUCCESS] Clicked on 'Aavri Hotel Deira, Dubai'")
        else:
            print("[ERROR] Could not find the hotel listing. It might not have loaded or requires scrolling.")
            # Fallback coordinate tap if text matching fails on the RecyclerView
            print("Attempting fallback tap on the first result area...")
            await device.tap(500, 800) # Approximate center of the first card
            
        # Step 4: Wait for Hotel Details page
        print("\n⏳ Waiting 5 seconds for Hotel Details to load...")
        await asyncio.sleep(5)
        
        # Step 5: Click "Choose my room"
        print("\n--- 4. Choosing Room ---")
        choose_room_btn = await device.find_element(text="Choose my room")
        if choose_room_btn:
            await choose_room_btn.click()
            print("[SUCCESS] Clicked 'Choose my room'")
        else:
            print("[ERROR] Could not find 'Choose my room' button. Falling back to coordinates.")
            # Bottom banner button usually sits around here on a 1080x2400 screen
            await device.tap(750, 2200) 
            
        # Step 6: Wait for Rooms list
        print("\n⏳ Waiting 5 seconds for Rooms to load...")
        await asyncio.sleep(5)
        
        # Step 7: Click "Book" on the first available room
        print("\n--- 5. Booking Room ---")
        book_btn = await device.find_element(text="Book")
        if book_btn:
            await book_btn.click()
            print("[SUCCESS] Clicked 'Book' button! Proceeding to guest details.")
        else:
            print("[ERROR] Could not find 'Book' button.")
            await device.tap(800, 2250) # Bottom right corner Book button fallback
            
        # Step 8: Extract Final Price
        print("\n⏳ Waiting 5 seconds for Price Details to load...")
        await asyncio.sleep(5)
        
        print("\n--- 6. Extracting Final Price ---")
        soup_price = await device.dump_hierarchy()
        price_nodes = soup_price.find_all("node", attrs={"text": True})
        
        final_price = None
        
        # Collect all AED prices we can find
        all_prices = []
        for node in price_nodes:
            text = node.get("text", "")
            if "AED" in text:
                print(f"Found related text: '{text}'")
                # Extract numbers from strings like "AED 107.31" or "AED 131"
                match = re.search(r'AED\s*([\d,]+\.?\d*)', text)
                if match:
                    try:
                        val = float(match.group(1).replace(',', ''))
                        all_prices.append((val, text))
                    except ValueError:
                        pass
                        
        if all_prices:
            # Sort by the extracted float value
            all_prices.sort(key=lambda x: x[0])
            # The lowest price is usually the final discounted price we want to pay
            final_price_val, final_price_text = all_prices[0]
            print(f"\n[SUCCESS] Extracted Final Booking Price: {final_price_text}")
        else:
            print("[ERROR] Could not extract a final price from the screen.")
            
        print("\n✅ Automated Agoda Flow Completed!")
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Automation failed: {e}")

if __name__ == "__main__":
    asyncio.run(automate_agoda_booking_flow())
