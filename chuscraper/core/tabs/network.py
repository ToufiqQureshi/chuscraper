from __future__ import annotations
from .base import TabMixin
from typing import TYPE_CHECKING, Dict, Optional, List

if TYPE_CHECKING:
    from ..tab import Tab

class NetworkMixin(TabMixin):
    async def set_extra_headers(self, headers: Dict[str, str]):
        """Sets extra HTTP headers for all requests."""
        # Use cdp types explicitly
        from ...cdp.network import Headers
        await self.send(self.cdp.network.set_extra_http_headers(Headers(headers)))

    async def enable_interception(self, patterns: List[Dict]):
        """Enables request interception with given patterns."""
        await self.send(self.cdp.fetch.enable(patterns=patterns))

    async def intercept_patterns(self, patterns: List[str], resource_types: List[str], action: str = "abort"):
        """
        Simplifies resource blocking.
        action: 'abort' or 'continue' (default)
        """
        # Use cdp types explicitly via self.cdp (module reference)
        cdp_patterns = []
        for p in patterns:
            for rt in resource_types:
                cdp_patterns.append(self.cdp.fetch.RequestPattern(
                    url_pattern=p,
                    resource_type=rt,
                    request_stage="Request"
                ))
        
        # Enable interception
        await self.enable_interception(cdp_patterns)
        
        # Register handler
        async def _handle_paused(event):
            try:
                if action == "abort":
                    await self.send(self.cdp.fetch.fail_request(
                        request_id=event.request_id,
                        error_reason="Aborted"
                    ))
                else:
                    await self.send(self.cdp.fetch.continue_request(
                        request_id=event.request_id
                    ))
            except Exception:
                pass

        self.tab.add_handler(self.cdp.fetch.RequestPaused, _handle_paused)

    async def get_performance_metrics(self):
        """Returns browser performance metrics."""
        # Fix: handle missing binding if domain isn't enabled
        try:
            return await self.send(self.cdp.performance.get_metrics())
        except AttributeError:
            # Fallback if domain binding missing from CDP generator
            res = await self.send({"method": "Performance.getMetrics", "params": {}})
            return res.get("metrics", [])
