from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from chuscraper.core.browser import Browser


@pytest.fixture
def mock_print(mocker: MockerFixture) -> Mock:
    return mocker.patch("builtins.print")


@pytest.fixture
def mock_start(mocker: MockerFixture, browser: Browser) -> Mock:
    return mocker.patch("chuscraper.start", return_value=browser)
