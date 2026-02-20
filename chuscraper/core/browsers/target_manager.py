from __future__ import annotations

import asyncio
import logging
import typing
from collections import defaultdict
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
        results = sorted(
            self.browser._targets, key=lambda x: x.type_ == "page", reverse=True
        )
        if len(results) > 0:
            result = results[0]
            from ..tab import Tab as TabClass

            if isinstance(result, TabClass):
                return result
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
                
                # Apply stealth/timezone to relevant targets only
                # Restricting to 'page' only to avoid crashing on short-lived iframes (ads/trackers)
                if target_info.type_ == "page":
                    asyncio.create_task(self.browser._apply_stealth_and_timezone(new_target))

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
        """Handles Target.attachedToTarget. Injects stealth scripts if waiting."""
        session_id = event.session_id
        target_info = event.target_info

        if event.waiting_for_debugger:
            try:
                if self.config.stealth:
                    from .. import stealth

                    # Pass detected browser version for coherence
                    browser_version = getattr(self, "version", None)
                    scripts, profile = stealth.get_stealth_scripts(self.config, browser_version)

                    # Only apply to 'page' to avoid crashing on short-lived iframes/workers
                    if target_info.type_ == "page":
                        # Apply CDP overrides for new targets
                        if self.config.user_agent:
                            await self.connection.send(
                                cdp.emulation.set_user_agent_override(
                                    user_agent=self.config.user_agent,
                                    accept_language=self.config.lang or "en-US",
                                    platform=profile.platform
                                ),
                                session_id=session_id
                            )

                        await self.connection.send(
                            cdp.emulation.set_device_metrics_override(
                                width=profile.screen_width,
                                height=profile.screen_height,
                                device_scale_factor=1,
                                mobile=False
                            ),
                            session_id=session_id
                        )

                        for script in scripts:
                            await self.connection.send(
                                cdp.page.add_script_to_evaluate_on_new_document(
                                    source=script,
                                    run_immediately=True # Ensure immediate execution for iframes
                                ),
                                session_id=session_id,
                            )
                    # We skip 'iframe', 'worker', 'service_worker' to prevent 404s and hangs
            except Exception as e:
                logger.error(
                    f"Failed to handle attached target {target_info.target_id}: {e}"
                )
            finally:
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
                await asyncio.sleep(0.01)
                if loop.time() - start_time > self.config.browser_connection_timeout:
                    raise asyncio.TimeoutError("Timeout waiting for new tab")

            await self.browser._apply_stealth_and_timezone(tab_obj)

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
        return await self.main_tab.get(url)  # type: ignore

    async def scrape(self, selector: str, timeout: typing.Union[int, float] = 10):
        """Shortcut for browser.main_tab.select(selector)."""
        return await self.main_tab.select(selector, timeout=timeout)  # type: ignore

    async def tile_windows(
        self, windows: typing.List[Tab] | None = None, max_columns: int = 0
    ) -> typing.List[typing.List[int]]:
        import math
        import mss

        m = mss.mss()
        screen_width, screen_height = None, None
        if m.monitors and len(m.monitors) >= 1:
            screen = m.monitors[0]
            screen_width = screen["width"]
            screen_height = screen["height"]
        if not screen_width or not screen_height:
            import warnings
            warnings.warn("no monitors detected")
            return []

        await self.update_targets()
        distinct_windows = defaultdict(list)

        tabs = windows if windows else self.tabs
        for tab_ in tabs:
            window_id, bounds = await tab_.get_window()
            distinct_windows[window_id].append(tab_)

        num_windows = len(distinct_windows)
        req_cols = max_columns or int(num_windows * (19 / 6))
        req_rows = int(num_windows / req_cols)

        while req_cols * req_rows < num_windows:
            req_rows += 1

        box_w = math.floor((screen_width / req_cols) - 1)
        box_h = math.floor(screen_height / req_rows)

        distinct_windows_iter = iter(distinct_windows.values())
        grid = []
        for x in range(req_cols):
            for y in range(req_rows):
                try:
                    tabs_to_tile = next(distinct_windows_iter)
                except StopIteration:
                    continue
                if not tabs_to_tile:
                    continue
                tab_to_tile = tabs_to_tile[0]

                try:
                    pos = [x * box_w, y * box_h, box_w, box_h]
                    grid.append(pos)
                    await tab_to_tile.set_window_size(*pos)
                except Exception:
                    logger.info("could not set window size.", exc_info=True)
                    continue
        return grid
