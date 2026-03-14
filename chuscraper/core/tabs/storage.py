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
        # Fix: match standard API and handle common missing params
        if 'url' not in kwargs and self.tab.url:
             kwargs['url'] = self.tab.url
        await self.send(self.cdp.network.set_cookie(name=name, value=value, **kwargs))

    async def clear_cookies(self):
        """Clears all session cookies."""
        await self.send(self.cdp.network.clear_browser_cookies())

    async def get_local_storage(self, key: Optional[str] = None) -> Union[Dict[str, str], str, None]:
        """Returns localStorage items via JS evaluation."""
        try:
            js = "JSON.stringify(localStorage)"
            res = await self.tab.evaluate(js)
            data = json.loads(res) if res else {}
            if key: return data.get(key)
            return data
        except Exception as e:
            logger.debug(f"get_local_storage failed: {e}")
            return {}

    async def set_local_storage(self, key: Union[str, Dict[str, str]], value: Optional[str] = None):
        """Sets localStorage items via JS evaluation."""
        items = key if isinstance(key, dict) else {key: value}
        for k, v in items.items():
            try:
                js = f"localStorage.setItem({json.dumps(k)}, {json.dumps(v)})"
                await self.tab.evaluate(js)
            except Exception as e:
                logger.debug(f"set_local_storage failed for {k}: {e}")

    async def set_user_agent(self, user_agent: Optional[str] = None, accept_language: Optional[str] = None, platform: Optional[str] = None):
        """Overrides user agent."""
        if not user_agent:
            user_agent = await self.tab.evaluate("navigator.userAgent")
        
        await self.send(self.cdp.network.set_user_agent_override(
            user_agent=user_agent or "",
            accept_language=accept_language,
            platform=platform
        ))
