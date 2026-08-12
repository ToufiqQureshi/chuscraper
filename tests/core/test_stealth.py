"""
Stealth engine tests.

This module previously imported `get_stealth_scripts`, a function that does not
exist anywhere in the codebase - so it failed at collection and had not run for
a long time. Rewritten against the actual SystemProfile API.
"""

import json
import sys

from chuscraper.core.config import Config
from chuscraper.core.stealth import BYPASS_FILES, SystemProfile, host_platform


def _profile(**kwargs) -> SystemProfile:
    # _fingerprint set so __post_init__ doesn't hit the network/browserforge
    kwargs.setdefault("user_agent", "Mozilla/5.0 Chrome/145.0.0.0 Safari/537.36")
    kwargs.setdefault("_fingerprint", {"User-Agent": kwargs["user_agent"]})
    return SystemProfile(**kwargs)


def test_stealth_adds_automation_controlled_flag() -> None:
    config = Config(stealth=True, browser_executable_path="/bin/true")
    assert "--disable-blink-features=AutomationControlled" in config()


def test_webdriver_bypass_is_included() -> None:
    scripts = _profile()._build_stealth_scripts(145, "145.0.0.0")
    combined = "\n".join(scripts)
    assert "webdriver" in combined


def test_every_bypass_file_is_loaded() -> None:
    """One entry for the config/hints preamble, plus one per bypass file."""
    scripts = _profile()._build_stealth_scripts(145, "145.0.0.0")
    assert len(scripts) == len(BYPASS_FILES) + 1


def test_bypass_can_be_disabled_via_stealth_options() -> None:
    profile = _profile(stealth_options={"patch_webdriver": False})
    scripts = profile._build_stealth_scripts(145, "145.0.0.0")
    assert len(scripts) == len(BYPASS_FILES)  # one fewer than the full set


def test_client_hints_do_not_touch_prototype_getter_directly() -> None:
    """
    Reading `Navigator.prototype.userAgentData` throws "Illegal invocation",
    which killed the entire client-hints script before it applied anything.
    """
    script = _profile()._build_hints_script(145, "145.0.0.0")
    assert "getOwnPropertyDescriptor(Navigator.prototype, 'userAgentData')" in script
    assert "if (Navigator.prototype.userAgentData)" not in script


def test_client_hints_report_the_real_host_platform() -> None:
    expected, _, _, _ = host_platform()
    script = _profile()._build_hints_script(145, "145.0.0.0")
    assert json.dumps(expected) in script

    if not sys.platform.startswith("win"):
        # the old code hardcoded Windows regardless of host
        assert 'platform: "Windows"' not in script


def test_version_flows_into_the_brand_list() -> None:
    script = _profile()._build_hints_script(131, "131.0.6778.86")
    assert '"131"' in script
    assert "131.0.6778.86" in script
