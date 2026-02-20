from chuscraper.core.config import Config


def test_production_ready_applies_resilient_defaults() -> None:
    config = Config(
        production_ready=True,
        browser_connection_timeout=0.1,
        browser_connection_max_tries=2,
        retry_timeout=5.0,
        retry_count=1,
        browser_executable_path="/bin/true",
    )

    assert config.retry_enabled is True
    assert config.retry_count >= 5
    assert config.retry_timeout >= 20.0
    assert config.browser_connection_timeout >= 0.5
    assert config.browser_connection_max_tries >= 20


def test_humanize_adds_window_flags_in_headful_mode() -> None:
    config = Config(humanize=True, headless=False, browser_executable_path="/bin/true")
    args = config()

    assert "--start-maximized" in args
    assert "--disable-popup-blocking" in args
