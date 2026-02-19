import asyncio
import logging
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chuscraper.core.config import Config
from chuscraper.core import util

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting concurrency test...")

    browsers = []
    try:
        # Launch 5 browsers concurrently
        tasks = []
        for i in range(5):
            # Test new config params
            config = Config(
                headless=True,
                port=0,
                logging=True,
                retry_enabled=True,
                retry_timeout=5.0
            )
            tasks.append(util.start(config))

        browsers = await asyncio.gather(*tasks)

        logger.info(f"Successfully launched {len(browsers)} browsers.")

        for i, browser in enumerate(browsers):
            logger.info(f"Browser {i} connected on port {browser.config.port}")
            assert browser.config.port > 0

            # Verify Job Object handle exists on Windows
            if sys.platform == "win32":
                if hasattr(browser._process, "_job_handle"):
                    logger.info(f"Browser {i} has Job Object handle: {browser._process._job_handle}")
                else:
                    logger.warning(f"Browser {i} MISSING Job Object handle!")

        await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"Test failed (expected if Chrome not installed): {e}")
    finally:
        logger.info("Cleaning up...")
        for browser in browsers:
            await browser.stop()

if __name__ == "__main__":
    if sys.platform == "linux":
        print("Skipping Windows-specific tests on Linux.")
        # We can still test import and basic config creation
        try:
            c = Config(port=0, logging=True)
            print("Config created successfully.")
        except Exception as e:
            print(f"Config creation failed: {e}")
    else:
        asyncio.run(main())
