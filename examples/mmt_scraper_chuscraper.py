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
        logging.FileHandler("mmt_chuscraper.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# Proxy configuration
PROXY_HOST = "gw.dataimpulse.com:823"
PROXY_USER = "11de131690b3fdc7ba16__cr.in"
PROXY_PASS = "e3e7d1a8f82bd8e3"

# Concurrency Control (Lower for MMT stability)
MAX_CONCURRENT_TABS = 2 
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TABS)

def get_proxy_url():
    timestamp = int(datetime.now().timestamp() * 1000) + random.randint(1000, 9999)
    return f"http://{PROXY_USER}_{timestamp}:{PROXY_PASS}@{PROXY_HOST}"

def get_dynamic_dates(offset):
    today = datetime.now()
    checkin = (today + timedelta(days=offset)).strftime("%m%d%Y")
    checkout = (today + timedelta(days=offset + 1)).strftime("%m%d%Y")
    return checkin, checkout

def update_url_dates(url, offset):
    checkin, checkout = get_dynamic_dates(offset)
    url = re.sub(r"checkin=\d{8}", f"checkin={checkin}", url)
    url = re.sub(r"checkout=\d{8}", f"checkout={checkout}", url)
    return url

async def human_jitter(page):
    await page.evaluate("""
        const jitter = () => {
            const event = new MouseEvent('mousemove', {
                view: window, bubbles: true, cancelable: true,
                clientX: Math.random() * (window.innerWidth / 2),
                clientY: Math.random() * (window.innerHeight / 2)
            });
            document.dispatchEvent(event);
        };
        for(let j=0; j<3; j++) setTimeout(jitter, j*300);
    """)

async def scrape_hotel_data(page, url):
    """Performs extraction using Chuscraper API with MMT flow."""
    try:
        # --- STEP 1: Session Warmup (RAW NAVIGATION) ---
        # Note: We use send(navigate) + sleep because MMT homepage never reaches 'idle' state.
        logging.info("🏠 Homepage Warmup: Navigating to MMT...")
        await page.send(cdp.page.navigate("https://www.makemytrip.com/"))
        
        # Hard wait instead of 'idle wait' for MMT
        await asyncio.sleep(random.uniform(5, 8))
        
        logging.info("🖱️  Simulating human activity...")
        await page.scroll_down(amount=random.randint(15, 30))
        await human_jitter(page)
        await asyncio.sleep(random.uniform(1, 3))
        
        # --- STEP 2: Navigate to Deep Link ---
        logging.info(f"🔗 Going to Hotel URL: {url[:60]}...")
        # Deep links usually load faster, we can use page.get here or send/wait
        await page.get(url) 
        
        # Extra wait for price render
        await asyncio.sleep(random.uniform(10, 15)) 

        content = await page.get_content()
        if "access denied" in content.lower() or "shield" in content.lower():
            logging.error("❌ Blocked by Akamai (Shield/Access Denied)")
            return {"status": "blocked", "reason": "shield_blocked"}

        data = {"URL": url}

        # --- Hotel Name ---
        try:
            name_el = await page.select('span.wordBreak.appendRight10[id^="htl_id_seo_"]')
            data["Hotel Name"] = name_el.text.strip() if name_el else "N/A"
        except:
            data["Hotel Name"] = "N/A"

        # --- Price / Sold Out ---
        try:
            sold_out_check = await page.select('p.font14.appendBottom5.redText.latoBold.lineHight17')
            if sold_out_check and "You Just Missed It" in sold_out_check.text:
                data["Hotel Price"] = "Sold out"
            else:
                price_el = await page.select('p.priceText.latoBlack.font22.blackText.appendBottom5[id="hlistpg_hotel_shown_price"]')
                data["Hotel Price"] = price_el.text.strip() if price_el else "N/A"
        except:
            data["Hotel Price"] = "N/A"

        # --- Rating ---
        try:
            rating_el = await page.select('span[itemprop="ratingValue"]')
            data["Rating"] = rating_el.text.strip() if rating_el else "N/A"
        except:
            data["Rating"] = "N/A"

        # --- Reviews ---
        try:
            review_el = await page.select('p.font14.darkGreyText.appendTop5 span[itemprop="reviewCount"]')
            data["Reviews"] = review_el.text.strip() if review_el else "N/A"
        except:
            data["Reviews"] = "N/A"

        if data["Hotel Name"] == "N/A":
            logging.warning("⚠️ Scrape finished but Hotel Name is 'N/A'. Likely load issue.")
            return {"status": "failed", "reason": "element_not_found"}

        logging.info(f"✅ Success: {data['Hotel Name']} | {data['Hotel Price']}")
        return {"status": "success", "data": data}

    except Exception as e:
        logging.error(f"❌ Scraper loop error: {e}")
        return {"status": "failed", "reason": str(e)}

async def process_single_url(browser, url, offset, idx, retries=2):
    """Handles logic for a single URL process with staggering."""
    # Stagger starts to avoid browser/proxy burst
    await asyncio.sleep(idx * 2.5) 
    
    updated_url = update_url_dates(url, offset)
    
    async with semaphore:
        for attempt in range(1, retries + 2):
            try:
                page = await browser.get("about:blank", new_tab=True)
                result = await scrape_hotel_data(page, updated_url)
                
                await page.close()
                if result["status"] == "success":
                    return result
                
                if result["status"] == "blocked":
                    logging.warning(f"🚫 Iteration {idx}, Attempt {attempt}: Blocked. Retrying...")
                    await asyncio.sleep(random.uniform(5, 10))
                    continue
                    
            except Exception as e:
                logging.error(f"⚠️ Task {idx} failed: {e}")
                
    return {"status": "failed", "reason": "max_retries"}

async def process_group(browser, group_id, urls, offset):
    tasks = []
    for i, url in enumerate(urls):
        tasks.append(process_single_url(browser, url, offset, i))
    
    results = await asyncio.gather(*tasks)
    return {f"Group_{group_id}": results}

def save_to_excel(all_data, filename_prefix):
    filename = f"{filename_prefix}.xlsx"
    try:
        with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
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
        logging.info(f"💾 Results saved to {filename}")
        return filename
    except Exception as e:
        logging.error(f"❌ Excel save failed: {e}")
        return None

async def main():
    YAML_FILE = "priya1.yaml"
    OFFSET = 0
    if not os.path.exists(YAML_FILE):
        logging.error(f"❌ {YAML_FILE} not found!")
        return

    with open(YAML_FILE, "r") as f:
        groups = yaml.safe_load(f)

    logging.info(f"🚀 Starting MMT Scraper... Groups: {len(groups)}")

    config = zd.Config(
        browser="chrome",
        headless=False,
        stealth=True,
        proxy=get_proxy_url()
    )

    all_results = OrderedDict()
    async with await zd.start(config) as browser:
        for idx, (group_id, urls) in enumerate(groups.items(), 1):
            logging.info(f"📊 Processing {group_id} ({idx}/{len(groups)})")
            group_results = await process_group(browser, group_id, urls, OFFSET)
            all_results.update(group_results)
            
            if idx < len(groups):
                await asyncio.sleep(random.uniform(5, 12))

    if all_results:
        save_to_excel(all_results, "mmt_final_results")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
