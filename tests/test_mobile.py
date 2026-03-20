import asyncio  
from chuscraper.mobile import MobileDevice  

async def main():  
    try:  
        # 1. Connect to your device (automatically finds first connected device)  
        device = await MobileDevice().connect()  
        print(f"[SUCCESS] Connected to device: {device.serial}")  
          
        # 2. Verify device is responsive by taking a screenshot  
        await device.screenshot("device_test.png")  
        print("[SUCCESS] Device is responsive - screenshot saved")  
          
        # 3. Example: Find and interact with elements  
        # Find search input by text  
        search_box = await device.find_element(text="Search")  
        if search_box:  
            await search_box.type("Your search query")  
            print("[SUCCESS] Typed in search box")  
          
        # Find button by resource-id (more reliable)  
        search_btn = await device.find_element(resource_id="com.app:id/search_button")  
        if search_btn:  
            await search_btn.click()  
            print("[SUCCESS] Clicked search button")  
        
        print("\n[WAITING] Waiting 10 seconds for results to load...")
        await asyncio.sleep(10)
        print("[SUCCESS] Finished waiting!\n")
          
        # 4. Extract data from multiple elements  
        results = await device.find_elements(class_name="android.widget.TextView")  
        for i, result in enumerate(results[:5]):  # Limit to first 5 results  
            text = result.get_text()  
            print(f"Result {i+1}: {text}")  
          
        # 5. Scroll down to load more content  
        width, height = 1080, 2400  # Adjust based on your device resolution  
        await device.swipe(width//2, height*0.8, width//2, height*0.2)  
        print("[SUCCESS] Scrolled down")  
          
    except RuntimeError as e:  
        if "No Android devices connected" in str(e):  
            print("[ERROR] No devices found. Please check:")  
            print("   - USB debugging is enabled")  
            print("   - Device is connected via USB")  
            print("   - Run 'adb devices' in terminal to verify")  
        else:  
            print(f"[ERROR] Error: {e}")  
    except Exception as e:  
        print(f"[ERROR] Unexpected error: {e}")  

if __name__ == "__main__":  
    asyncio.run(main())