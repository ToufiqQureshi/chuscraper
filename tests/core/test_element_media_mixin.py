from chuscraper.core.element import Element


def test_element_exposes_media_methods_from_modular_mixin() -> None:
    assert hasattr(Element, "screenshot_b64")
    assert hasattr(Element, "save_screenshot")
    assert hasattr(Element, "record_video")
    assert hasattr(Element, "is_recording")
