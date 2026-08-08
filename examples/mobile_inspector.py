import asyncio
from chuscraper.mobile import MobileDevice
import json

async def inspect():
    device = await MobileDevice().connect()
    print(f"Connected to {device.serial}")

    print("\nScanning screen for clickable elements...")
    elements = await device.get_clickable_elements()

    print("-" * 100)
    print(f"{'Index':<5} | {'Text':<20} | {'Resource ID':<40} | {'XPath Index'}")
    print("-" * 100)

    for el in elements:
        text = (el['text'][:18] + '..') if len(el['text']) > 20 else el['text']
        res_id = (el['resource_id'][-38:] if len(el['resource_id']) > 40 else el['resource_id'])
        xpath = el['xpath']
        print(f"{el['index']:<5} | {text:<20} | {res_id:<40} | {xpath}")

    print("-" * 100)
    print("\nScreenshot saved as inspect_screen.png for visual reference.")
    await device.screenshot("inspect_screen.png")

if __name__ == "__main__":
    asyncio.run(inspect())
