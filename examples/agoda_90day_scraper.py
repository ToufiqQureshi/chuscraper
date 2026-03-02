import asyncio
import os
import time
import csv
from datetime import datetime, timedelta
from chuscraper.mobile import MobileDevice

# --- CONFIGURATION ---
HOTEL_NAME = "Aavri Hotel"
DAYS_TO_SCRAPE = 90
OUTPUT_FILE = "agoda_prices.csv"

# --- TIPS ---
# Use examples/mobile_inspector.py to find the EXACT index or XPath
# of the button if multiple buttons have the same text.

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
            # 1. Select Date Picker
            # If multiple 'Mar' elements exist, we can use an index: (//node[contains(@text, 'Mar')])[1]
            date_picker = await device.find_element(xpath="(//node[contains(@text, 'Mar') or contains(@text, 'Feb')])[1]")
            if date_picker:
                await date_picker.click()
                await asyncio.sleep(2)

            # 2. Select Days (Using exact text for day numbers)
            # To be precise, we look for nodes that are clickable AND have the day text
            checkin_el = await device.find_element(xpath=f"//node[@text='{checkin_date.day}' and @clickable='true']")
            if checkin_el:
                await checkin_el.click()
                await asyncio.sleep(1)

            checkout_el = await device.find_element(xpath=f"//node[@text='{checkout_date.day}' and @clickable='true']")
            if checkout_el:
                await checkout_el.click()

            # Confirm dates (Try Update button)
            confirm_btn = await device.find_element(xpath="//node[@text='Update' or @text='Select' or @text='Apply']")
            if confirm_btn:
                await confirm_btn.click()
                await asyncio.sleep(1)

            # 3. Click SEARCH
            # If there are multiple Search buttons, use indexing: (//node[@text='Search'])[1]
            search_btn = await device.wait_for_element(xpath="(//node[@text='Search'])[1]", timeout=5)
            await search_btn.click()
            print("Searching...")

            # 4. Find Hotel and extract Price
            hotel_el = await device.wait_for_element(query=HOTEL_NAME, timeout=15)
            if hotel_el:
                print(f"Found {HOTEL_NAME}!")
                await hotel_el.click()
                await asyncio.sleep(5)

                # Extract Price near specific currency/symbol
                price_el = await device.find_element(xpath="(//node[contains(@text, 'AED') or contains(@text, '₹')])[1]")
                if price_el:
                    price_text = price_el.get_text()
                    print(f"Price for {date_str}: {price_text}")
                    with open(OUTPUT_FILE, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([date_str, HOTEL_NAME, price_text, "Success"])

            # Return to search
            await device.press_keycode(4) # BACK
            await asyncio.sleep(2)

        except Exception as e:
            print(f"Error on {date_str}: {e}")
            with open(OUTPUT_FILE, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([date_str, HOTEL_NAME, "N/A", f"Error: {str(e)}"])

            # Recovery: Go home and re-launch
            await device.press_keycode(3)
            await asyncio.sleep(2)
            await device._adb_cmd("shell", "monkey", "-p", "com.agoda.mobile.consumer", "1")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(scrape_agoda())
