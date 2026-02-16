import asyncio
import os
import random
import logging
import re
import yaml
import tempfile
import shutil
import pandas as pd
from datetime import datetime, timedelta
from collections import OrderedDict
import chuscraper as zd
from chuscraper import cdp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agoda_chuscraper.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# Proxy configuration
PROXY_HOST = "gw.dataimpulse.com:823"
PROXY_USER = "11de131690b3fdc7ba16__cr.in"
PROXY_PASS = "e3e7d1a8f82bd8e3"

# Concurrency Control
MAX_CONCURRENT_TABS = 8
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TABS)

def get_proxy_url():
    """Generates a unique proxy rotation URL."""
    timestamp = int(datetime.now().timestamp() * 1000) + random.randint(1000, 9999)
    return f"http://{PROXY_USER}_{timestamp}:{PROXY_PASS}@{PROXY_HOST}"

def get_dynamic_dates(offset):
    today = datetime.now()
    checkin = (today + timedelta(days=offset)).strftime("%Y-%m-%d")
    checkout = (today + timedelta(days=offset + 1)).strftime("%Y-%m-%d")
    return checkin, checkout

def update_url_dates(url, offset):
    checkin, checkout = get_dynamic_dates(offset)
    url = re.sub(r"checkIn=\d{4}-\d{2}-\d{2}", f"checkIn={checkin}", url)
    url = re.sub(r"checkOut=\d{4}-\d{2}-\d{2}", f"checkOut={checkout}", url)
    return url

async def block_resources(page):
    """Blocks images and fonts for faster loading."""
    try:
        await page.send(cdp.network.set_blocked_urls(urls=[
            "*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp", "*.svg", "*.woff", "*.woff2", "*.ttf"
        ]))
    except Exception as e:
        logging.debug(f"Resource blocking error: {e}")

async def scrape_hotel_data(page, url):
    """Performs extraction using Chuscraper API."""
    try:
        logging.info(f"📍 Navigating to: {url[:100]}...")
        
        # Navigate with domcontentloaded for speed
        # Note: Chuscraper's get/navigate waits for load by default
        await page.get(url)
        await asyncio.sleep(random.uniform(4, 7)) # Allow JS to settle

        content = await page.get_content()
        if "access denied" in content.lower() or "blocked" in content.lower():
            return {"status": "blocked", "reason": "shield_blocked"}

        # Wait for key element
        try:
            await page.wait_for(selector='[data-selenium="hotel-name"]', timeout=30)
        except:
            # Fallback
            await page.wait_for(selector='[data-element-name="PropertyCardBaseJacket"]', timeout=15)

        data = {"URL": url}

        # --- Hotel Name ---
        try:
            name_el = await page.select('[data-selenium="hotel-name"]')
            data["Hotel Name"] = name_el.text.strip() if name_el else "Unknown"
        except:
            data["Hotel Name"] = "Unknown"

        # --- Price ---
        try:
            sold_out = "Sold out" in content
            if sold_out:
                data["Hotel Price"] = "Sold out"
            else:
                price_el = await page.select('[data-selenium="display-price"]')
                data["Hotel Price"] = price_el.text.strip() if price_el else "N/A"
        except:
            data["Hotel Price"] = "N/A"

        # --- Rating ---
        try:
            rating_container = await page.select('[data-element-name="property-card-review"]')
            if rating_container:
                match = re.search(r"(\d\.\d)", rating_container.text)
                data["Rating"] = match.group(1) if match else "N/A"
            else:
                data["Rating"] = "N/A"
        except:
            data["Rating"] = "N/A"

        # --- Reviews ---
        try:
            review_container = await page.select('[data-element-name="property-card-review"]')
            if review_container:
                match = re.search(r"(\d+\s*reviews)", review_container.text, re.IGNORECASE)
                data["Reviews"] = match.group(1) if match else "N/A"
            else:
                data["Reviews"] = "N/A"
        except:
            data["Reviews"] = "N/A"

        return {"status": "success", "data": data}

    except Exception as e:
        logging.error(f"❌ Error during scrape: {e}")
        return {"status": "failed", "reason": str(e)}

async def process_single_url(browser, url, offset, retries=2):
    """Handles logic for a single URL process."""
    updated_url = update_url_dates(url, offset)
    
    async with semaphore:
        for attempt in range(1, retries + 2):
            try:
                # Open a new tab for each URL to ensure fresh session/stealth per site
                page = await browser.get("about:blank", new_tab=True)
                await block_resources(page)
                
                # Randomized human delay
                await asyncio.sleep(random.uniform(1, 3))
                
                result = await scrape_hotel_data(page, updated_url)
                
                if result["status"] == "success":
                    await page.close()
                    return result
                
                await page.close()
                if result["status"] == "blocked":
                    logging.warning(f"🚫 Iteration {attempt}: Blocked, retrying with new IP...")
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
                    
            except Exception as e:
                logging.error(f"⚠️ Attempt {attempt} failed: {e}")
                
    return {"status": "failed", "reason": "max_retries"}

async def process_group(browser, group_id, urls, offset):
    """Processes a group of URLs concurrently."""
    tasks = []
    for url in urls:
        tasks.append(process_single_url(browser, url, offset))
    
    results = await asyncio.gather(*tasks)
    
    successful_data = [r["data"] for r in results if r["status"] == "success"]
    
    hotel_name = "Unknown"
    if successful_data:
        hotel_name = successful_data[0].get("Hotel Name", "Unknown")
        
    return {f"Group_{group_id}_{hotel_name}": results}

def save_to_excel(all_data, filename_prefix):
    """Saves the collected data to an Excel file."""
    filename = f"{filename_prefix}.xlsx"
    try:
        with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
            total_hotels = 0
            for group_name, results in all_data.items():
                successful_data = [r["data"] for r in results if r["status"] == "success"]
                if successful_data:
                    df = pd.DataFrame(successful_data)
                    cols = ["Hotel Name", "Hotel Price", "Rating", "Reviews", "URL"]
                    for col in cols:
                        if col not in df.columns: df[col] = "N/A"
                    df = df[cols]
                    
                    sheet_name = re.sub(r'[\\/*?:"<>|]', "_", group_name)[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    total_hotels += len(successful_data)
                    
        logging.info(f"💾 Saved to {filename}. Total hotels: {total_hotels}")
        return filename
    except Exception as e:
        logging.error(f"❌ Excel save failed: {e}")
        return None

async def main():
    YAML_FILE = "priya3_agoda.yaml"
    OFFSET = 0
    
    if not os.path.exists(YAML_FILE):
        logging.error(f"❌ YAML file '{YAML_FILE}' not found!")
        return

    with open(YAML_FILE, "r") as f:
        groups = yaml.safe_load(f)

    logging.info(f"🚀 Starting Chuscraper Agoda Migration for {len(groups)} groups...")

    # Configure Browser
    config = zd.Config(
        browser="chrome",
        headless=False,
        stealth=True,
        proxy=get_proxy_url() # This user/pass will be updated per rotation if needed, 
                              # but Chuscraper currently binds proxy to Browser instance.
                              # To rotate per tab, we'd need multiple browser instances or session support.
                              # For now, we'll use one high-quality rotation session.
    )

    all_results = OrderedDict()
    
    async with await zd.start(config) as browser:
        for idx, (group_id, urls) in enumerate(groups.items(), 1):
            logging.info(f"📊 Processing {group_id} ({idx}/{len(groups)})")
            
            group_results = await process_group(browser, group_id, urls, OFFSET)
            all_results.update(group_results)
            
            if idx < len(groups):
                delay = random.uniform(5, 10)
                logging.info(f"😴 Resting {delay:.1f}s between groups...")
                await asyncio.sleep(delay)

    if all_results:
        save_to_excel(all_results, "agoda_results_chuscraper")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
