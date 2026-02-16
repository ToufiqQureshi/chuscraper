# 🌍 Real-World Scraper Examples

We have included 5 powerful, ready-to-use examples for scraping major e-commerce and travel platforms.
These scripts demonstrate `chuscraper`'s ability to handle dynamic content, bot protection (like PerimeterX/Akamai), and strict IP filtering.

## 🚀 How to Run

All examples are located in the `examples/` directory.
Run them using Python:

```bash
python examples/amazon_search_product.py
```

> **⚠️ IMPORTANT:**
> These sites have strict anti-bot systems. You **MUST** use a high-quality Residential Proxy.
> The examples include a working proxy (`gw.dataimpulse.com`) for demonstration, but you should replace it with your own for production use.

---

## 📦 The Examples

### 1. Amazon Product Search
**File:** `examples/amazon_search_product.py`
- **Target:** Amazon.in / Amazon.com
- **Mode:** Hybrid (AI + Standard)
- **Features:** 
  - **Standard Mode:** Uses `wait_for_selector`, `type`, and `click` to search without API keys.
  - **AI Mode:** Uses `ai_pilot` and `ai_extract` for deeper analysis if key is present.
  - Bypasses "Dog" pages using Native Chrome + Stealth.

### 2. Flipkart Laptop Scraper
**File:** `examples/flipkart_scraper.py`
- **Target:** Flipkart.com
- **Mode:** Hybrid (AI + Standard)
- **Features:**
  - Handles login popups automatically using standard selectors.
  - **Standard Mode:** Extracts product list using `query_selector_all`.
  - **AI Mode:** Intelligently parses specs and discounts.

### 3. MakeMyTrip Flights
**File:** `examples/makemytrip_flight_search.py`
- **Target:** MakeMyTrip.com (Flights)
- **Mode:** Hybrid (AI + Standard)
- **Features:**
  - **Standard Mode:** Smart fallback to pre-filled search URLs to avoid complex form scripting.
  - **AI Mode:** Uses `ai_pilot` to negotiate the complex React-based flight search form.
  - Extracts Airline, Price, and Duration.

### 4. Walmart Search
**File:** `examples/walmart_search.py`
- **Target:** Walmart.com
- **Mode:** Hybrid (AI + Standard)
- **Features:**
  - **Standard Mode:** Uses `page.type` and `page.send_keys("Enter")` for search.
  - **AI Mode:** Uses LLM to extract structured product data (Shipping, Availability).
  - Bypasses PerimeterX (Px) using stealth config.

### 5. Google Shopping Compare
**File:** `examples/google_shopping_compare.py`
- **Target:** Google Shopping
- **Mode:** Hybrid (AI + Standard)
- **Features:**
  - **Standard Mode:** Hand-coded logic to click "Reject all" on cookie banners.
  - **AI Mode:** Uses Vision/LLM to understand and extract comparison tables.
  - Compares prices across multiple stores.

---

## 🛠️ Configuration
Each script uses a standardized `Config`:
```python
config = zd.Config(
    browser="chrome",       # Native Chrome for trust
    headless=False,         # Headless often triggers strict checks
    stealth=True,           # Enable all evasion modules
    disable_webgl=True,     # Prevent hardware leaks
    proxy="YOUR_PROXY_URL"  # Residential proxy is key
)
```
