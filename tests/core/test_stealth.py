from chuscraper.core.config import Config
from chuscraper.core.stealth import get_stealth_scripts


def test_webdriver_patch_uses_undefined_and_non_enumerable() -> None:
    config = Config(stealth=True, browser_executable_path="/bin/true")
    scripts, _ = get_stealth_scripts(config, browser_version="124.0.6367.119")
    combined = "\n".join(scripts)

    assert "get: () => undefined" in combined
    assert "enumerable: false" in combined


def test_stealth_adds_automation_controlled_flag() -> None:
    config = Config(stealth=True, browser_executable_path="/bin/true")

    assert "--disable-blink-features=AutomationControlled" in config()
