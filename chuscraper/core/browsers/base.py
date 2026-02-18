from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from ...core.browser import Browser
    from ...core.connection import Connection
    from ...core.config import Config


class BrowserMixin:
    """
    Base class for Browser Mixins.
    Provides shared access to the Browser instance and its core components.
    """
    _browser: Browser

    @property
    def browser(self) -> Browser:
        return self._browser

    @property
    def config(self) -> Config:
        return self._browser._config

    @property
    def connection(self) -> Connection | None:
        return self._browser._connection

    async def send(self, command: typing.Any, **kwargs: typing.Any) -> typing.Any:
        if not self.connection:
            raise RuntimeError("Browser connection not initialized")
        return await self.connection.send(command, **kwargs)
