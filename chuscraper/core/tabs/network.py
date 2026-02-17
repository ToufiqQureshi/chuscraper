from __future__ import annotations
from .base import TabMixin
from typing import TYPE_CHECKING, Dict, Optional, List

if TYPE_CHECKING:
    from ..tab import Tab

class NetworkMixin(TabMixin):
    async def set_extra_headers(self, headers: Dict[str, str]):
        """Sets extra HTTP headers for all requests."""
        await self.send(self.cdp.network.set_extra_http_headers(headers))

    async def enable_interception(self, patterns: List[Dict]):
        """Enables request interception with given patterns."""
        await self.send(self.cdp.fetch.enable(patterns=patterns))

    async def get_performance_metrics(self):
        """Returns browser performance metrics."""
        return await self.send(self.cdp.performance.get_metrics())
