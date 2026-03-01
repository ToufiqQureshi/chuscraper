import asyncio
import os
import logging
import sys
import chuscraper as zd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def run_test():
    logger.info("🚀 Starting Chuscraper Interaction Test - Final Attempt (Fixed Send)")

    results = []

    def record(func, status, error=None, reason=None):
        results.append({
            "Function": func,
            "Status": "PASS" if status else "FAIL",
            "Error": error or "-",
            "Reason": reason or "-"
        })
        if status:
            logger.info(f"✅ {func} PASSED")
        else:
            logger.error(f"❌ {func} FAILED: {error}")

    browser = None
    try:
        browser = await zd.start(headless=True, stealth=True)
        page = browser.main_tab
        logger.info("🌐 Browser started.")

        # 2. Test: goto (Navigation)
        try:
            await page.goto("https://NEUROFIQ.in")
            # ReadyState check
            for _ in range(20):
                rs = await page.evaluate("document.readyState")
                if rs == "complete":
                    break
                await asyncio.sleep(0.5)
            record("goto", True)
        except Exception as e:
            record("goto", False, str(e), "Navigation failed")

        # 3. Test: wait_for
        try:
            # We use evaluate to check if it exists before wait_for
            await page.wait_for(selector="nav", timeout=10)
            record("wait_for", True)
        except Exception as e:
            record("wait_for", False, str(e), "Element 'nav' not found")

        # 4. Test: hover
        try:
            # We need to use query_selector and then hover on the element
            # because tab.hover() uses select() which might fail if CDP is weird
            el = await page.select("nav a[href='#services']")
            if el:
                await el.hover()
                record("hover", True)
            else:
                record("hover", False, "Element not found")
        except Exception as e:
            record("hover", False, str(e), "Hover action failed")

        # 5. Test: click
        try:
            el = await page.select("nav a[href='#contact']")
            if el:
                await el.click()
                await asyncio.sleep(2)
                record("click", True)
            else:
                record("click", False, "Element not found")
        except Exception as e:
            record("click", False, str(e), "Click action failed")

        # 6. Test: scroll_into_view
        try:
            form_el = await page.select("#contactForm")
            if form_el:
                await form_el.scroll_into_view()
                record("scroll_into_view", True)
            else:
                record("scroll_into_view", False, "Form #contactForm not found")
        except Exception as e:
            record("scroll_into_view", False, str(e), "Scroll into view failed")

        # 7. Test: type
        try:
            el = await page.select("#name")
            if el:
                await el.type("Jules Test")
                record("type", True)
            else:
                record("type", False, "Input #name not found")
        except Exception as e:
            record("type", False, str(e), "Type action failed")

        # 8. Test: fill
        try:
            el = await page.select("#email")
            if el:
                await el.fill("jules@example.com")
                record("fill", True)
            else:
                record("fill", False, "Input #email not found")
        except Exception as e:
            record("fill", False, str(e), "Fill action failed")

        # 9. Test: select_option
        try:
            select_el = await page.select("#service")
            if select_el:
                options = await select_el.query_selector_all("option")
                if len(options) > 1:
                    await options[1].select_option()
                    record("select_option", True)
                else:
                    record("select_option", False, "No options found")
            else:
                record("select_option", False, "Select #service not found")
        except Exception as e:
            record("select_option", False, str(e), "Select option failed")

        # 10. Test: mouse_drag (drag_and_drop)
        try:
            logo = await page.select("nav img")
            if logo:
                await logo.mouse_drag(destination=(50, 50), relative=True)
                record("mouse_drag", True)
            else:
                record("mouse_drag", False, "Logo not found")
        except Exception as e:
            record("mouse_drag", False, str(e), "Mouse drag failed")

        # 11. Test: Form Submit (Clicking the button)
        try:
            submit_btn = await page.select("#contactForm button[type='submit']")
            if submit_btn:
                await submit_btn.click(mode="human")
                record("submit (click)", True)
            else:
                record("submit (click)", False, "Submit button not found")
        except Exception as e:
            record("submit (click)", False, str(e), "Submit button click failed")

    except Exception as e:
        logger.error(f"💥 Critical Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if browser:
            await browser.stop()

        # Print Summary Table
        print("\n" + "="*80)
        print(f"{'Function':<20} | {'Status':<10} | {'Error':<20} | {'Reason':<20}")
        print("-" * 80)
        for res in results:
            print(f"{res['Function']:<20} | {res['Status']:<10} | {str(res['Error'])[:20]:<20} | {str(res['Reason'])[:20]:<20}")
        print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(run_test())
