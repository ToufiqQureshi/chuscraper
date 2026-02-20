import asyncio

from chuscraper.core.util import start


def test_start_forwards_stealth_and_humanize_options(monkeypatch):
    captured = {}

    async def fake_create(config):
        captured["config"] = config
        return "ok"

    monkeypatch.setattr("chuscraper.core.browser.Browser.create", fake_create)

    result = asyncio.run(
        start(
            browser_executable_path="/bin/true",
            stealth=True,
            stealth_options={"patch_webdriver": True, "patch_canvas": False},
            humanize=True,
            production_ready=True,
            browser_connection_timeout=0.6,
            browser_connection_max_tries=25,
        )
    )

    assert result == "ok"
    config = captured["config"]
    assert config.stealth is True
    assert config.stealth_options["patch_canvas"] is False
    assert config.humanize is True
    assert config.production_ready is True
    assert config.browser_connection_timeout == 0.6
    assert config.browser_connection_max_tries == 25
