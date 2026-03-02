import asyncio
import os
import time
import csv
from datetime import datetime, timedelta
from chuscraper.mobile import MobileDevice

# --- CONFIGURATION ---
HOTEL_NAME = "Aavri Hotel"  # Specify the hotel you want to track
DAYS_TO_SCRAPE = 90
OUTPUT_FILE = "agoda_prices.csv"

async def scrape_agoda():
    device = await MobileDevice().connect()
    print(f"Connected to {device.serial}")

    # Initialize CSV
    with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Hotel", "Price", "Status"])

    current_date = datetime.now()

    for i in range(DAYS_TO_SCRAPE):
        checkin_date = current_date + timedelta(days=i)
        checkout_date = checkin_date + timedelta(days=1)

        date_str = checkin_date.strftime("%Y-%m-%d")
        print(f"\n--- Scraping for {date_str} ---")

        try:
            # 1. Reset to 'All rooms' screen or Home if needed
            # For now, we assume we're on the screen where search can be initiated

            # 2. Click on Date Selection (usually shows current dates)
            # We use 'query' to find elements containing date text or 'Mon, Mar 02' format
            # Or use coordinates if the layout is very stable
            date_picker = await device.find_element(query="Mar") # Partial match for month
            if date_picker:
                await date_picker.click()
                await asyncio.sleep(2)

            # 3. Select Dates in Calendar
            # This is app-specific. Typically involves clicking the day number.
            # Example: find element with text "2" (the day)
            day_el = await device.find_element(text=str(checkin_date.day))
            if day_el:
                await day_el.click()
                # Wait a bit and click checkout day
                await asyncio.sleep(1)
                checkout_el = await device.find_element(text=str(checkout_date.day))
                if checkout_el:
                    await checkout_el.click()

            # Confirm dates (Look for 'Update' or 'Apply' or 'Select')
            confirm_btn = await device.find_element(query="Update") or await device.find_element(query="Select")
            if confirm_btn:
                await confirm_btn.click()
                await asyncio.sleep(1)

            # 4. Click SEARCH
            search_btn = await device.wait_for_element(query="Search", timeout=5)
            await search_btn.click()
            print("Searching...")

            # 5. Wait for Results and find Hotel
            # We wait for the hotel name to appear
            hotel_el = await device.wait_for_element(query=HOTEL_NAME, timeout=15)
            if hotel_el:
                print(f"Found {HOTEL_NAME}!")
                # Sometimes we need to click it to see the final price
                await hotel_el.click()
                await asyncio.sleep(5)

                # 6. Extract Price
                # Prices usually have currency symbols like 'AED' or '₹'
                # We can use XPath to find a node near 'Total price' or similar
                price_el = await device.find_element(xpath="//node[contains(@text, 'AED') or contains(@text, '₹')]")
                if price_el:
                    price_text = price_el.get_text()
                    print(f"Price for {date_str}: {price_text}")

                    # Save to CSV
                    with open(OUTPUT_FILE, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([date_str, HOTEL_NAME, price_text, "Success"])
                else:
                    print(f"Could not find price for {date_str}")

            # Go back to search screen for next iteration
            await device.press_keycode(4) # BACK
            await asyncio.sleep(2)
            await device.press_keycode(4) # BACK (if still in details)
            await asyncio.sleep(1)

        except Exception as e:
            print(f"Error on {date_str}: {e}")
            with open(OUTPUT_FILE, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([date_str, HOTEL_NAME, "N/A", f"Error: {str(e)}"])

            # Try to recover by going back to home
            await device.press_keycode(3) # HOME
            await asyncio.sleep(5)
            # Re-open Agoda (requires package name)
            await device._adb_cmd("shell", "monkey", "-p", "com.agoda.mobile.consumer", "-c", "android.intent.category.LAUNCHER", "1")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(scrape_agoda())
