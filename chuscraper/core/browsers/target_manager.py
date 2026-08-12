from __future__ import annotations

import asyncio
import logging
import typing
from .base import BrowserMixin
from ... import cdp
from .. import util

if typing.TYPE_CHECKING:
    from ...core.tab import Tab
    from ...core.connection import Connection

logger = logging.getLogger(__name__)


class TargetManagerMixin(BrowserMixin):
    @property
    def main_tab(self) -> Tab | None:
        """returns the target which was launched with the browser"""
        from ..tab import Tab as TabClass

        # Only ever hand back an actual page. The old sort put pages first but
        # still returned results[0] when there were none, so callers could get
        # an iframe/worker target back as the "main tab".
        for target in self.browser._targets:
            if target.type_ == "page" and isinstance(target, TabClass):
                return target
        return None

    @property
    def tabs(self) -> typing.List[Tab]:
        """returns the current targets which are of type "page\""""
        tabs = filter(lambda item: item.type_ == "page", self.browser._targets)
        return list(tabs)  # type: ignore

    async def _handle_target_update(
        self,
        event: typing.Union[
            cdp.target.TargetInfoChanged,
            cdp.target.TargetDestroyed,
            cdp.target.TargetCreated,
            cdp.target.TargetCrashed,
        ],
    ) -> None:
        """internal handler which updates the targets when chrome emits events"""

        async with self.browser._update_target_info_mutex:
            if isinstance(event, cdp.target.TargetInfoChanged):
                target_info = event.target_info

                current_tab = next(
                    (
                        item
                        for item in self.browser._targets
                        if item.target_id == target_info.target_id
                    ),
                    None,
                )
                if not current_tab:
                    logger.debug(
                        f"TargetInfoChanged for unknown target {target_info.target_id}"
                    )
                    return

                current_target = current_tab.target

                if logger.getEffectiveLevel() <= 10:
                    changes = util.compare_target_info(current_target, target_info)
                    changes_string = ""
                    for change in changes:
                        key, old, new = change
                        changes_string += f"\n{key}: {old} => {new}\n"
                    logger.debug(
                        "target #%d has changed: %s"
                        % (self.browser._targets.index(current_tab), changes_string)
                    )

                current_tab.target = target_info

            elif isinstance(event, cdp.target.TargetCreated):
                target_info = event.target_info
                
                # CRITICAL FIX: Ignore iframes/workers to prevent 404 connection crashes
                if target_info.type_ != "page":
                    return

                # update_targets() polling and this event can both see the same
                # new target, which used to append it twice.
                if any(t.target_id == target_info.target_id for t in self.browser._targets):
                    return

                from ..tab import Tab

                new_target = Tab(
                    (
                        f"ws://{self.config.host}:{self.config.port}"
                        f"/devtools/{target_info.type_ or 'page'}"
                        f"/{target_info.target_id}"
                    ),
                    target=target_info,
                    browser=self.browser,
                )

                self.browser._targets.append(new_target)
                

                logger.debug(
                    "target #%d created => %s", len(self.browser._targets), new_target
                )

            elif isinstance(event, cdp.target.TargetDestroyed):
                current_tab = next(
                    (
                        item
                        for item in self.browser._targets
                        if item.target_id == event.target_id
                    ),
                    None,
                )
                if current_tab:
                    logger.debug(
                        "target removed. id # %d => %s"
                        % (self.browser._targets.index(current_tab), current_tab)
                    )
                    self.browser._targets.remove(current_tab)

            elif isinstance(event, cdp.target.TargetCrashed):
                logger.error(
                    f"CRITICAL: Target Crashed! ID: {event.target_id} Status: {event.status} Error: {event.error_code}"
                )
                current_tab = next(
                    (
                        item
                        for item in self.browser._targets
                        if item.target_id == event.target_id
                    ),
                    None,
                )
                if current_tab:
                    logger.warning(f"Removing crashed target from list: {current_tab}")
                    self.browser._targets.remove(current_tab)

    async def _handle_attached_to_target(
        self, event: cdp.target.AttachedToTarget
    ) -> None:
        """Handles Target.attachedToTarget. Resumes execution if waiting for debugger."""
        session_id = event.session_id

        if event.waiting_for_debugger:
            # ALWAYS RESUME execution, otherwise the tab hangs forever
            try:
                await self.connection.send(
                    cdp.runtime.run_if_waiting_for_debugger(), session_id=session_id
                )
            except Exception:
                pass

    async def _get_targets(self) -> typing.List[cdp.target.TargetInfo]:
        if not self.connection:
            raise RuntimeError("Browser connection not initialized")
        info = await self.connection.send(cdp.target.get_targets(), _is_update=True)
        return info

    async def update_targets(self) -> None:
        targets: typing.List[cdp.target.TargetInfo]
        targets = await self._get_targets()
        from ..tab import Tab as TabClass

        for t in targets:
            for existing_tab in self.browser._targets:
                if existing_tab.target_id == t.target_id:
                    existing_tab.target.__dict__.update(t.__dict__)
                    break
            else:
                self.browser._targets.append(
                    TabClass(
                        (
                            f"ws://{self.config.host}:{self.config.port}"
                            f"/devtools/page"
                            f"/{t.target_id}"
                        ),
                        target=t,
                        browser=self.browser,
                    )
                )

        await asyncio.sleep(0)

    async def get(
        self, url: str = "about:blank", new_tab: bool = False, new_window: bool = False
    ) -> Tab:
        """convience function known from selenium."""
        if new_window and not new_tab:
            new_tab = True

        if not self.tabs or new_tab:
            target = await self.send(
                cdp.target.create_target(
                    "about:blank", new_window=new_window, background=False
                )
            )

            loop = asyncio.get_running_loop()
            start_time = loop.time()
            while True:
                tab_obj = next(
                    (t for t in self.tabs if t.target_id == target),
                    None,
                )
                if tab_obj:
                    break

                # Bug #3 Fallback: Explicitly poll if event-based discovery is slow
                if loop.time() - start_time > 1.0:
                    await self.update_targets()

                await asyncio.sleep(0.1)
                if loop.time() - start_time > self.config.browser_connection_timeout + 5.0:
                    raise asyncio.TimeoutError("Timeout waiting for new tab")


            if url != "about:blank":
                await tab_obj.get(url)
            return tab_obj

        else:
            p = self.main_tab
            if not p:
                return await self.get(url, new_tab=True)
            await p.get(url)
            return p

    async def goto(self, url: str) -> Tab:
        """Shortcut for browser.main_tab.get(url)."""
        # main_tab can legitimately be None (all tabs closed); calling .get() on
        # it raised an opaque NoneType AttributeError. Open one instead.
        tab = self.main_tab
        if tab is None:
            return await self.get(url, new_tab=True)
        return await tab.get(url)

    async def scrape(self, selector: str, timeout: typing.Union[int, float] = 10):
        """Shortcut for browser.main_tab.select(selector)."""
        if not self.main_tab: return None
        return await self.main_tab.select(selector, timeout=timeout)
