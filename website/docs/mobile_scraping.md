---
sidebar_position: 6
---

# Mobile Scraping (ADB)

Chuscraper allows you to scrape data from native Android applications using ADB (Android Debug Bridge). This enables automation of any installed app, including those without a web version.

## Prerequisites

Before you start, ensure you have:

1.  **Android SDK Platform-Tools (ADB):** Installed and added to your system PATH.
    *   [Download ADB](https://developer.android.com/studio/releases/platform-tools)
2.  **Android Device/Emulator:**
    *   **Physical Device:** Enable "Developer Options" -> "USB Debugging".
    *   **Emulator:** Start an AVD via Android Studio.
3.  **USB Connection:** Connect your device to the computer. Verify with `adb devices` in your terminal.

## Quick Start

Here is a simple example to search for a hotel in a travel app:

```python
import asyncio
from chuscraper.mobile import MobileDevice

async def main():
    # Connect to the first available device
    device = await MobileDevice().connect()
    print(f"Connected to: {device.serial}")

    # 1. Open the App (manually or via adb shell am start)
    # Assume the app is open on the home screen

    # 2. Find and Click 'Search' Box
    # Using text visible on screen
    search_box = await device.find_element(text="Where to?")
    if search_box:
        await search_box.type("Goa")
        # Press Enter/Search on keyboard
        await device.press_keycode(66)

    # 3. Select a Hotel from Results
    # Wait for results to load
    await asyncio.sleep(5)

    # Using Resource ID (more reliable)
    first_hotel = await device.find_element(resource_id="com.travel.app:id/hotel_name")
    if first_hotel:
        print(f"Found Hotel: {first_hotel.get_text()}")
        await first_hotel.click()

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### `MobileDevice`

The main class to control the device.

| Method | Description |
| :--- | :--- |
| `connect(serial=None)` | Connects to a device. If `serial` is omitted, connects to the first available device. |
| `find_element(**kwargs)` | Finds a single element. Returns `MobileElement` or `None`. |
| `find_elements(**kwargs)` | Finds all matching elements. Returns `List[MobileElement]`. |
| `tap(x, y)` | Taps at the specified coordinates. |
| `swipe(x1, y1, x2, y2)` | Swipes from (x1, y1) to (x2, y2). Useful for scrolling. |
| `input_text(text)` | Types text into the currently focused field. |
| `press_keycode(code)` | Simulates a hardware key press (e.g., `3` for Home, `4` for Back). |
| `screenshot(filename)` | Saves a screenshot of the current screen. |
| `dump_hierarchy()` | Returns the raw XML hierarchy as a BeautifulSoup object. |

### `MobileElement`

Represents a UI component on the screen.

| Method | Description |
| :--- | :--- |
| `click()` | Calculates the center of the element's bounds and taps it. |
| `type(text)` | Clicks the element and then types the text. |
| `get_text()` | Returns the visible text or content description. |
| `get_attribute(name)` | Returns the value of an attribute (e.g., `resource-id`, `checked`). |

## Finding Elements

You can find elements using various attributes present in the Android XML dump:

*   **By Text:** `device.find_element(text="Login")`
*   **By Resource ID:** `device.find_element(resource_id="com.example:id/btn_submit")`
*   **By Content Description:** `device.find_element(content_desc="Navigate up")`
*   **By Class:** `device.find_element(class_name="android.widget.Button")`

> **Tip:** Use `await device.dump_hierarchy()` to inspect the XML structure and find the correct attributes for your target app.

## Advanced Usage

### Looping Through Lists

To scrape a list of items (e.g., hotel prices), you can loop through elements found by a common Resource ID:

```python
prices = await device.find_elements(resource_id="com.hotel.app:id/price_text")

print("--- Prices on Screen ---")
for price in prices:
    print(price.get_text())

# Scroll down to load more
width, height = 1080, 2400 # Adjust based on device
await device.swipe(width//2, height*0.8, width//2, height*0.2)
```

### Handling Dynamic Content

Mobile apps often take time to load data. Always use `asyncio.sleep()` or a retry loop when waiting for a new screen to appear.

```python
import asyncio

# Wait for 'Payment' screen
for _ in range(10):
    if await device.find_element(text="Payment Details"):
        break
    await asyncio.sleep(1)
```

## Troubleshooting

*   **Device Not Found:** Ensure USB Debugging is ON and the device is authorized (check phone screen for a popup). run `adb devices` in terminal.
*   **Element Not Found:** The screen might not be fully loaded. Increase wait times. Also, some apps use `WebViews` or `Flutter` which might not expose standard Android XML nodes.
*   **Text Input Issues:** `input_text` simulates keyboard input. Ensure the field is focused (clicked) before typing.
*   **Special Characters:** ADB input has limited support for complex characters or emojis. Use `adb shell input keyboard text "..."` for better compatibility if simple text fails.
*   **Screen State:** Ensure the device screen is ON and unlocked. Consider setting "Screen Timeout" to "Never" in developer settings.
*   **Performance:** Dumping XML hierarchy can be slow (1-2s) on older devices. Avoid calling `dump_hierarchy()` inside tight loops; fetch it once and parse locally.
