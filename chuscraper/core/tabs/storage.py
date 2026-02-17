from __future__ import annotations
from .base import TabMixin
import json
from typing import TYPE_CHECKING, List, Dict

if TYPE_CHECKING:
    from ..tab import Tab

class StorageMixin(TabMixin):
    async def get_cookies(self) -> List[Dict]:
        """Returns all cookies for the current page."""
        res = await self.send(self.cdp.network.get_cookies())
        return [c.to_json() if hasattr(c, "to_json") else c for c in res]

    async def set_cookie(self, name: str, value: str, **kwargs):
        """Sets a cookie."""
        await self.send(self.cdp.network.set_cookie(name, value, **kwargs))

    async def clear_cookies(self):
        """Clears all session cookies."""
        await self.send(self.cdp.network.clear_browser_cookies())

    async def get_local_storage(self) -> Dict[str, str]:
        """Returns localStorage items as dict."""
        if self.tab.target is None or not self.tab.url:
            await self.tab.wait()
        
        origin = "/".join(self.tab.url.split("/", 3)[:-1] if self.tab.url else [])
        items = await self.send(self.cdp.dom_storage.get_dom_storage_items(
            self.cdp.dom_storage.StorageId(is_local_storage=True, security_origin=origin)
        ))
        retval: Dict[str, str] = {}
        for item in items:
            retval[item[0]] = item[1]
        return retval

    async def set_local_storage(self, items: Dict[str, str]):
        """Sets localStorage items."""
        if self.tab.target is None or not self.tab.url:
            await self.tab.wait()
        
        origin = "/".join(self.tab.url.split("/", 3)[:-1] if self.tab.url else [])
        await asyncio.gather(*[
            self.send(self.cdp.dom_storage.set_dom_storage_item(
                storage_id=self.cdp.dom_storage.StorageId(is_local_storage=True, security_origin=origin),
                key=str(key), value=str(val)
            )) for key, val in items.items()
        ])

    async def set_user_agent(self, user_agent: Optional[str] = None, accept_language: Optional[str] = None, platform: Optional[str] = None):
        """Overrides user agent."""
        if not user_agent:
            user_agent = await self.tab.evaluate("navigator.userAgent")
        
        await self.send(self.cdp.network.set_user_agent_override(
            user_agent=user_agent or "",
            accept_language=accept_language,
            platform=platform
        ))
