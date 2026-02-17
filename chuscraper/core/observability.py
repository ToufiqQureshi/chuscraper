import json
import logging
import os
import datetime
import pathlib
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class Logger:
    @staticmethod
    def setup(level: int = logging.INFO):
        logging.basicConfig(
            level=level,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )

class FailureDumper:
    """Production monitor that dumps page state and screenshots on failure."""
    def __init__(self, dump_dir: str = "dumps"):
        self.dump_dir = pathlib.Path(dump_dir)
        self.dump_dir.mkdir(exist_ok=True)

    async def dump(self, tab: Any, error: Exception, context: str = "failure"):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{context}_{timestamp}"
        
        dump_path = self.dump_dir / prefix
        dump_path.mkdir(exist_ok=True)
        
        logger.error(f"🚨 Production Failure Detected! Dumping state to {dump_path}")
        
        try:
            # 1. Page Content
            content = await tab.get_content()
            with open(dump_path / "content.html", "w", encoding="utf-8") as f:
                f.write(content)
                
            # 2. Screenshot
            screenshot = await tab.screenshot()
            with open(dump_path / "screenshot.png", "wb") as f:
                f.write(screenshot)
                
            # 3. Metadata
            meta = {
                "url": tab.url,
                "error": str(error),
                "timestamp": timestamp,
                "context": context
            }
            with open(dump_path / "metadata.json", "w") as f:
                json.dump(meta, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to create complete failure dump: {e}")

def get_observability_context():
    """Returns basic structured context for logging."""
    return {
        "pii_filtered": True,
        "mode": os.environ.get("CHUSCRAPER_MODE", "production")
    }
