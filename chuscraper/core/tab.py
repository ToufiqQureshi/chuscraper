from __future__ import annotations

import asyncio
import base64
import datetime
import logging
import random
import time
import pathlib
import re
import secrets
import typing
import urllib.parse
import warnings
import webbrowser
from typing import TYPE_CHECKING, Any, List, Literal, Optional, Tuple, Union, cast, Type, TypeVar

from .intercept import BaseFetchInterception
from .. import cdp
from . import element, util
from .config import PathLike
from .connection import Connection, ProtocolException
from .expect import DownloadExpectation, RequestExpectation, ResponseExpectation
from ..cdp.fetch import RequestStage
from ..cdp.network import ResourceType
from ..cdp.runtime import DeepSerializedValue
from ..extractors.markdown import html_to_markdown
from .humanizer import Humanizer
from pydantic import BaseModel

from .tabs.navigation import NavigationMixin
from .tabs.dom import DomMixin
from .tabs.actions import ActionsMixin
from .tabs.network import NetworkMixin
from .tabs.wait import WaitMixin
from .tabs.storage import StorageMixin
from .tabs.screenshot import ScreenshotMixin
from .tabs.evaluation import EvaluationMixin

if TYPE_CHECKING:
    from .browser import Browser
    from .element import Element

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class Tab(
    Connection, 
    NavigationMixin, 
    DomMixin, 
    ActionsMixin, 
    NetworkMixin, 
    WaitMixin, 
    StorageMixin, 
    ScreenshotMixin, 
    EvaluationMixin
):
    """
    :ref:`tab` is the controlling mechanism/connection to a 'target',
    for most of us 'target' can be read as 'tab'. however it could also
    be an iframe, serviceworker or background script for example,
    although there isn't much to control for those.

    if you open a new window by using :py:meth:`browser.get(..., new_window=True)`
    your url will open a new window. this window is a 'tab'.
    When you browse to another page, the tab will be the same (it is an browser view).

    So it's important to keep some reference to tab objects, in case you're
    done interacting with elements and want to operate on the page level again.

    Custom CDP commands
    ---------------------------
    Tab object provide many useful and often-used methods. It is also
    possible to utilize the included cdp classes to to something totally custom.

    the cdp package is a set of so-called "domains" with each having methods, events and types.
    to send a cdp method, for example :py:obj:`cdp.page.navigate`, you'll have to check
    whether the method accepts any parameters and whether they are required or not.

    you can use

    ```python
    await tab.send(cdp.page.navigate(url='https://yoururlhere'))
    ```

    so tab.send() accepts a generator object, which is created by calling a cdp method.
    this way you can build very detailed and customized commands.
    (note: finding correct command combo's can be a time consuming task, luckily i added a whole bunch
    of useful methods, preferably having the same api's or lookalikes, as in selenium)


    some useful, often needed and simply required methods
    ===================================================================


    :py:meth:`~find`  |  find(text)
    ----------------------------------------
    find and returns a single element by text match. by default returns the first element found.
    much more powerful is the best_match flag, although also much more expensive.
    when no match is found, it will retry for <timeout> seconds (default: 10), so
    this is also suitable to use as wait condition.


    :py:meth:`~find` |  find(text, best_match=True) or find(text, True)
    ---------------------------------------------------------------------------------
    Much more powerful (and expensive!!) than the above, is the use of the `find(text, best_match=True)` flag.
    It will still return 1 element, but when multiple matches are found, picks the one having the
    most similar text length.
    How would that help?
    For example, you search for "login", you'd probably want the "login" button element,
    and not thousands of scripts,meta,headings which happens to contain a string of "login".

    when no match is found, it will retry for <timeout> seconds (default: 10), so
    this is also suitable to use as wait condition.


    :py:meth:`~select` | select(selector)
    ----------------------------------------
    find and returns a single element by css selector match.
    when no match is found, it will retry for <timeout> seconds (default: 10), so
    this is also suitable to use as wait condition.


    :py:meth:`~select_all` | select_all(selector)
    ------------------------------------------------
    find and returns all elements by css selector match.
    when no match is found, it will retry for <timeout> seconds (default: 10), so
    this is also suitable to use as wait condition.


    await :py:obj:`Tab`
    ---------------------------
    calling `await tab` will do a lot of stuff under the hood, and ensures all references
    are up to date. also it allows for the script to "breathe", as it is oftentime faster than your browser or
    webpage. So whenever you get stuck and things crashes or element could not be found, you should probably let
    it "breathe"  by calling `await page`  and/or `await page.sleep()`

    also, it's ensuring :py:obj:`~url` will be updated to the most recent one, which is quite important in some
    other methods.

    Using other and custom CDP commands
    ======================================================
    using the included cdp module, you can easily craft commands, which will always return an generator object.
    this generator object can be easily sent to the :py:meth:`~send`  method.

    :py:meth:`~send`
    ---------------------------
    this is probably THE most important method, although you won't ever call it, unless you want to
    go really custom. the send method accepts a :py:obj:`cdp` command. Each of which can be found in the
    cdp section.

    when you import * from this package, cdp will be in your namespace, and contains all domains/actions/events
    you can act upon.
    """

    browser: Browser | None

    def __init__(
        self,
        websocket_url: str,
        target: cdp.target.TargetInfo,
        browser: Browser | None = None,
        **kwargs: Any,
    ):
        super().__init__(websocket_url, target, browser, **kwargs)
        self.browser = browser
        self._dom = None
        self._window_id = None
        # Track last mouse position for human-like movements (default to top-left safe zone)
        self._last_mouse_x = 0
        self._last_mouse_y = 0
        self._is_stopped = False
        self._timeout = 30.0
        self._download_behavior = None
        self.enabled_domains = []

    @property
    def cdp(self):
        """Shortcut to access cdp domains"""
        return cdp

    @property
    def timeout(self) -> float:
        return self._timeout

    @timeout.setter
    def timeout(self, value: float):
        self._timeout = value

    @property
    def url(self) -> str:
        """Returns the current URL of the tab."""
        if not self.target:
            return ""
        return self.target.url

    @property
    def inspector_url(self) -> str:
        if not self.browser:
            raise ValueError("this tab has no browser attribute")
        return f"http://{self.browser.config.host}:{self.browser.config.port}/devtools/inspector.html?ws={self.websocket_url[5:]}"





    async def close(self):
        """Closes the tab/target."""
        if self.browser:
            await self.send(cdp.target.close_target(self.target_id))

    async def stop(self):
        """Cleanup resources."""
        await self.close()

    async def xpath(self, xpath: str) -> List[Element]:
        """
        Evaluate an XPath expression and return matching elements.

        :param xpath: The XPath expression.
        :return: A list of Element objects.
        """
        doc = await self.send(cdp.dom.get_document(-1, True))
        search_id, result_count = await self.send(cdp.dom.perform_search(xpath, include_user_agent_shadow_dom=True))

        if result_count == 0:
            return []

        node_ids = await self.send(cdp.dom.get_search_results(search_id, 0, result_count))
        await self.send(cdp.dom.discard_search_results(search_id))

        elements = []
        for node_id in node_ids:
            try:
                node = util.filter_recurse(doc, lambda n: n.node_id == node_id)
                if node:
                    elements.append(element.create(node, self, doc))
            except Exception:
                pass

        return elements











    async def close(self) -> None:
        """
        close the current target (ie: tab,window,page)
        :return:
        :rtype:
        :raises asyncio.TimeoutError:
        :raises RuntimeError:
        """

        if not self.browser or not self.browser.connection:
            raise RuntimeError("Browser not yet started. use await browser.start()")

        future = asyncio.get_running_loop().create_future()
        event_type = cdp.target.TargetDestroyed

        async def close_handler(event: cdp.target.TargetDestroyed) -> None:
            if future.done():
                return

            if self.target and event.target_id == self.target.target_id:
                future.set_result(event)

        self.browser.connection.add_handler(event_type, close_handler)

        if self.target and self.target.target_id:
            await self.send(cdp.target.close_target(target_id=self.target.target_id))

        await asyncio.wait_for(future, 10)
        self.browser.connection.remove_handlers(event_type, close_handler)

    async def get_window(self) -> Tuple[cdp.browser.WindowID, cdp.browser.Bounds]:
        """
        get the window Bounds
        :return:
        :rtype:
        """
        window_id, bounds = await self.send(
            cdp.browser.get_window_for_target(self.target_id)
        )
        return window_id, bounds

    async def get_content(self) -> str:
        """
        gets the current page source content (html)
        :return:
        :rtype:
        """
        doc: cdp.dom.Node = await self.send(cdp.dom.get_document(-1, True))
        return await self.send(
            cdp.dom.get_outer_html(backend_node_id=doc.backend_node_id)
        )

    async def maximize(self) -> None:
        """
        maximize page/tab/window
        """
        return await self.set_window_state(state="maximize")

    async def minimize(self) -> None:
        """
        minimize page/tab/window
        """
        return await self.set_window_state(state="minimize")

    async def fullscreen(self) -> None:
        """
        minimize page/tab/window
        """
        return await self.set_window_state(state="fullscreen")

    async def medimize(self) -> None:
        return await self.set_window_state(state="normal")

    async def set_window_size(
        self, left: int = 0, top: int = 0, width: int = 1280, height: int = 1024
    ) -> None:
        """
        set window size and position

        :param left: pixels from the left of the screen to the window top-left corner
        :param top: pixels from the top of the screen to the window top-left corner
        :param width: width of the window in pixels
        :param height: height of the window in pixels
        :return:
        :rtype:
        """
        return await self.set_window_state(left, top, width, height)

    async def activate(self) -> None:
        """
        active this target (ie: tab,window,page)
        """
        if self.target is None:
            raise ValueError("target is none")
        await self.send(cdp.target.activate_target(self.target.target_id))

    async def bring_to_front(self) -> None:
        """
        alias to self.activate
        """
        await self.activate()

    async def set_window_state(
        self,
        left: int = 0,
        top: int = 0,
        width: int = 1280,
        height: int = 720,
        state: str = "normal",
    ) -> None:
        """
        sets the window size or state.

        for state you can provide the full name like minimized, maximized, normal, fullscreen, or
        something which leads to either of those, like min, mini, mi,  max, ma, maxi, full, fu, no, nor
        in case state is set other than "normal", the left, top, width, and height are ignored.

        :param left: desired offset from left, in pixels
        :param top: desired offset from the top, in pixels
        :param width: desired width in pixels
        :param height: desired height in pixels
        :param state:
            can be one of the following strings:
                - normal
                - fullscreen
                - maximized
                - minimized
        """
        available_states = ["minimized", "maximized", "fullscreen", "normal"]
        window_id: cdp.browser.WindowID
        bounds: cdp.browser.Bounds
        (window_id, bounds) = await self.get_window()

        for state_name in available_states:
            if all(x in state_name for x in state.lower()):
                break
        else:
            raise NameError(
                "could not determine any of %s from input '%s'"
                % (",".join(available_states), state)
            )
        window_state = getattr(
            cdp.browser.WindowState, state_name.upper(), cdp.browser.WindowState.NORMAL
        )
        if window_state == cdp.browser.WindowState.NORMAL:
            bounds = cdp.browser.Bounds(left, top, width, height, window_state)
        else:
            # min, max, full can only be used when current state == NORMAL
            # therefore we first switch to NORMAL
            await self.set_window_state(state="normal")
            bounds = cdp.browser.Bounds(window_state=window_state)

        await self.send(cdp.browser.set_window_bounds(window_id, bounds=bounds))

    async def scroll_down(self, amount: int = 25, speed: int = 800) -> None:
        """
        scrolls down maybe

        :param amount: number in percentage. 25 is a quarter of page, 50 half, and 1000 is 10x the page
        :param speed: number swipe speed in pixels per second (default: 800).
        :return:
        :rtype:
        """
        window_id: cdp.browser.WindowID
        bounds: cdp.browser.Bounds
        (window_id, bounds) = await self.get_window()
        height = bounds.height if bounds.height else 0

        await self.send(
            cdp.input_.synthesize_scroll_gesture(
                x=0,
                y=0,
                y_distance=-(height * (amount / 100)),
                y_overscroll=0,
                x_overscroll=0,
                prevent_fling=True,
                repeat_delay_ms=0,
                speed=speed,
            )
        )
        await asyncio.sleep(height * (amount / 100) / speed)

    async def scroll_up(self, amount: int = 25, speed: int = 800) -> None:
        """
        scrolls up maybe

        :param amount: number in percentage. 25 is a quarter of page, 50 half, and 1000 is 10x the page
        :param speed: number swipe speed in pixels per second (default: 800).
        :return:
        :rtype:
        """
        window_id: cdp.browser.WindowID
        bounds: cdp.browser.Bounds
        (window_id, bounds) = await self.get_window()
        height = bounds.height if bounds.height else 0

        await self.send(
            cdp.input_.synthesize_scroll_gesture(
                x=0,
                y=0,
                y_distance=(height * (amount / 100)),
                x_overscroll=0,
                prevent_fling=True,
                repeat_delay_ms=0,
                speed=speed,
            )
        )
        await asyncio.sleep(height * (amount / 100) / speed)

    async def wait_for(
        self,
        selector: str | None = None,
        text: str | None = None,
        timeout: int | float = 10,
    ) -> Element:
        """
        variant on query_selector_all and find_elements_by_text
        this variant takes either selector or text, and will block until
        the requested element(s) are found.

        it will block for a maximum of <timeout> seconds, after which
        a TimeoutError will be raised

        :param selector: css selector
        :param text: text
        :param timeout:
        :return:
        :rtype: Element
        :raises asyncio.TimeoutError:
        """
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        if selector:
            item = await self.query_selector(selector)
            while not item and loop.time() - start_time < timeout:
                item = await self.query_selector(selector)
                await self.sleep(0.5)

            if item:
                return item
        if text:
            item = await self.find_element_by_text(text)
            while not item and loop.time() - start_time < timeout:
                item = await self.find_element_by_text(text)
                await self.sleep(0.5)

            if item:
                return item

        raise asyncio.TimeoutError("time ran out while waiting")

    async def wait_for_ready_state(
        self,
        until: Literal["loading", "interactive", "complete"] = "interactive",
        timeout: int = 10,
    ) -> bool:
        """
        Waits for the page to reach a certain ready state.
        :param until: The ready state to wait for. Can be one of "loading", "interactive", or "complete".
        :param timeout: The maximum number of seconds to wait.
        :raises asyncio.TimeoutError: If the timeout is reached before the ready state is reached.
        :return: True if the ready state is reached.
        :rtype: bool
        """
        loop = asyncio.get_event_loop()
        start_time = loop.time()

        while True:
            ready_state = await self.evaluate("document.readyState")
            if ready_state == until:
                return True

            if loop.time() - start_time > timeout:
                raise asyncio.TimeoutError(
                    "time ran out while waiting for load page until %s" % until
                )

            await asyncio.sleep(0.1)

    def expect_request(
        self, url_pattern: Union[str, re.Pattern[str]]
    ) -> RequestExpectation:
        """
        Creates a request expectation for a specific URL pattern.
        :param url_pattern: The URL pattern to match requests.
        :return: A RequestExpectation instance.
        :rtype: RequestExpectation
        """
        return RequestExpectation(self, url_pattern)

    def expect_response(
        self, url_pattern: Union[str, re.Pattern[str]]
    ) -> ResponseExpectation:
        """
        Creates a response expectation for a specific URL pattern.
        :param url_pattern: The URL pattern to match responses.
        :return: A ResponseExpectation instance.
        :rtype: ResponseExpectation
        """
        return ResponseExpectation(self, url_pattern)

    def expect_download(self) -> DownloadExpectation:
        """
        Creates a download expectation for next download.
        :return: A DownloadExpectation instance.
        :rtype: DownloadExpectation
        """
        return DownloadExpectation(self)

    def intercept(
        self,
        url_pattern: str,
        request_stage: RequestStage,
        resource_type: ResourceType,
    ) -> BaseFetchInterception:
        """
        Sets up interception for network requests matching a URL pattern, request stage, and resource type.

        :param url_pattern: URL string or regex pattern to match requests.
        :param request_stage: Stage of the request to intercept (e.g., request, response).
        :param resource_type: Type of resource (e.g., Document, Script, Image).
        :return: A BaseFetchInterception instance for further configuration or awaiting intercepted requests.
        :rtype: BaseFetchInterception

        Use this to block, modify, or inspect network traffic for specific resources during browser automation.
        """
        return BaseFetchInterception(self, url_pattern, request_stage, resource_type)

    async def download_file(
        self, url: str, filename: Optional[PathLike] = None
    ) -> None:
        """
        downloads file by given url.

        :param url: url of the file
        :param filename: the name for the file. if not specified the name is composed from the url file name
        """
        if not self._download_behavior:
            directory_path = pathlib.Path.cwd() / "downloads"
            directory_path.mkdir(exist_ok=True)
            await self.set_download_path(directory_path)

            warnings.warn(
                f"no download path set, so creating and using a default of"
                f"{directory_path}"
            )
        if not filename:
            filename = url.rsplit("/")[-1]
            filename = filename.split("?")[0]

        code = """
         (elem) => {
            async function _downloadFile(
              imageSrc,
              nameOfDownload,
            ) {
              const response = await fetch(imageSrc);
              const blobImage = await response.blob();
              const href = URL.createObjectURL(blobImage);

              const anchorElement = document.createElement('a');
              anchorElement.href = href;
              anchorElement.download = nameOfDownload;

              document.body.appendChild(anchorElement);
              anchorElement.click();

              setTimeout(() => {
                document.body.removeChild(anchorElement);
                window.URL.revokeObjectURL(href);
                }, 500);
            }
            _downloadFile('%s', '%s')
            }
            """ % (
            url,
            filename,
        )

        body = (await self.query_selector_all("body"))[0]
        await body.update()
        await self.send(
            cdp.runtime.call_function_on(
                code,
                object_id=body.object_id,
                arguments=[cdp.runtime.CallArgument(object_id=body.object_id)],
            )
        )

    async def save_snapshot(self, filename: str = "snapshot.mhtml") -> None:
        """
        Saves a snapshot of the page.
        :param filename: The save path; defaults to "snapshot.mhtml"
        """
        await self.sleep()  # update the target's url
        path = pathlib.Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = await self.send(cdp.page.capture_snapshot())
        if not data:
            raise ProtocolException(
                "Could not take snapshot. Most possible cause is the page has not finished loading yet."
            )

        with open(filename, "w") as file:
            file.write(data)

    async def screenshot_b64(
        self,
        format: str = "jpeg",
        full_page: bool = False,
    ) -> str:
        """
        Takes a screenshot of the page and return the result as a base64 encoded string.
        This is not the same as :py:obj:`Element.screenshot_b64`, which takes a screenshot of a single element only

        :param format: jpeg or png (defaults to jpeg)
        :param full_page: when False (default) it captures the current viewport. when True, it captures the entire page
        :return: screenshot data as base64 encoded
        :rtype: str
        """
        if self.target is None:
            raise ValueError("target is none")

        await self.sleep()  # update the target's url

        if format.lower() in ["jpg", "jpeg"]:
            format = "jpeg"
        elif format.lower() in ["png"]:
            format = "png"

        data = await self.send(
            cdp.page.capture_screenshot(
                format_=format, capture_beyond_viewport=full_page
            )
        )
        if not data:
            raise ProtocolException(
                "could not take screenshot. most possible cause is the page has not finished loading yet."
            )

        return data

    async def save_screenshot(
        self,
        filename: Optional[PathLike] = "auto",
        format: str = "jpeg",
        full_page: bool = False,
    ) -> str:
        """
        Saves a screenshot of the page.
        This is not the same as :py:obj:`Element.save_screenshot`, which saves a screenshot of a single element only

        :param filename: uses this as the save path
        :param format: jpeg or png (defaults to jpeg)
        :param full_page: when False (default) it captures the current viewport. when True, it captures the entire page
        :return: the path/filename of saved screenshot
        :rtype: str
        """
        if format.lower() in ["jpg", "jpeg"]:
            ext = ".jpg"

        elif format.lower() in ["png"]:
            ext = ".png"

        if not filename or filename == "auto":
            assert self.target is not None
            parsed = urllib.parse.urlparse(self.target.url)
            parts = parsed.path.split("/")
            last_part = parts[-1]
            last_part = last_part.rsplit("?", 1)[0]
            dt_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            candidate = f"{parsed.hostname}__{last_part}_{dt_str}"
            path = pathlib.Path(candidate + ext)  # noqa
        else:
            path = pathlib.Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = await self.screenshot_b64(format=format, full_page=full_page)

        data_bytes = base64.b64decode(data)
        if not path:
            raise RuntimeError("invalid filename or path: '%s'" % filename)
        path.write_bytes(data_bytes)
        return str(path)

    async def print_to_pdf(self, filename: PathLike, **kwargs: Any) -> pathlib.Path:
        """
        Prints the current page to a PDF file and saves it to the specified path.

        :param filename: The path where the PDF will be saved.
        :param kwargs: Additional options for printing to be passed to :py:obj:`cdp.page.print_to_pdf`.
        :return: The path to the saved PDF file.
        :rtype: pathlib.Path
        """
        filename = pathlib.Path(filename)
        if filename.is_dir():
            raise ValueError(
                f"filename {filename} must be a file path, not a directory"
            )

        data, _ = await self.send(cdp.page.print_to_pdf(**kwargs))

        data_bytes = base64.b64decode(data)
        filename.write_bytes(data_bytes)
        return filename

    async def set_download_path(self, path: PathLike) -> None:
        """
        sets the download path and allows downloads
        this is required for any download function to work (well not entirely, since when unset we set a default folder)

        :param path:
        :return:
        :rtype:
        """
        path = pathlib.Path(path)
        await self.send(
            cdp.browser.set_download_behavior(
                behavior="allow", download_path=str(path.resolve())
            )
        )
        self._download_behavior = ["allow", str(path.resolve())]

    async def get_all_linked_sources(self) -> List[Element]:
        """
        get all elements of tag: link, a, img, scripts meta, video, audio

        :return:
        """
        all_assets = await self.query_selector_all(selector="a,link,img,script,meta")
        return [element.create(asset.node, self) for asset in all_assets]

    async def get_all_urls(self, absolute: bool = True) -> List[str]:
        """
        convenience function, which returns all links (a,link,img,script,meta)

        :param absolute: try to build all the links in absolute form instead of "as is", often relative
        :return: list of urls
        """

        import urllib.parse

        res: list[str] = []
        all_assets = await self.query_selector_all(selector="a,link,img,script,meta")
        for asset in all_assets:
            if not absolute:
                res_to_add = asset.src or asset.href
                if res_to_add:
                    res.append(res_to_add)
            else:
                for k, v in asset.attrs.items():
                    if k in ("src", "href"):
                        if "#" in v:
                            continue
                        if not any([_ in v for _ in ("http", "//", "/")]):
                            continue
                        abs_url = urllib.parse.urljoin(
                            "/".join(self.url.rsplit("/")[:3] if self.url else []), v
                        )
                        if not abs_url.startswith(("http", "//", "ws")):
                            continue
                        res.append(abs_url)
        return res

    async def verify_cf(
        self,
        click_delay: float = 5,
        timeout: float = 15,
        challenge_selector: Optional[str] = None,
        flash_corners: bool = False,
    ) -> None:
        """
        Finds and solves the Cloudflare checkbox challenge.

        The total time for finding and clicking is governed by `timeout`.

        Args:
            click_delay: The delay in seconds between clicks.
            timeout: The total time in seconds to wait for the challenge and solve it.
            challenge_selector: An optional CSS selector for the challenge input element.
            flash_corners: If True, flash the corners of the challenge element.

        Raises:
            TimeoutError: If the checkbox is not found or solved within the timeout.
        """
        from .cloudflare import verify_cf

        await verify_cf(self, click_delay, timeout, challenge_selector, flash_corners)


    # Storage and Network overrides are now in mixins

    async def markdown(self) -> str:
        """
        Converts the current page content to clean, LLM-ready Markdown.
        """
        content = await self.get_content()
        return html_to_markdown(content)


    async def crawl(self, depth: int = 1, max_pages: int = 5) -> List[str]:
        """
        Simple crawler that visits links on the current page.

        Args:
            depth: How deep to crawl (currently only supports 1 - shallow crawl of links on current page)
            max_pages: Limit number of pages to visit

        Returns:
            List of visited URLs
        """
        # TODO: Implement full recursive crawler with queue
        # For now, implemented a "map" feature essentially
        links = await self.get_all_urls()

        # Filter external links?
        current_host = urllib.parse.urlparse(self.url).hostname

        visited = []
        count = 0
        for link in links:
            if count >= max_pages:
                break
            if urllib.parse.urlparse(link).hostname == current_host:
                visited.append(link)
                # In a real crawler, we would navigate here and extract
                count += 1

        return visited

    async def __call__(
        self,
        text: str | None = None,
        selector: str | None = None,
        timeout: int | float = 10,
    ) -> Element:
        """
        alias to query_selector_all or find_elements_by_text, depending
        on whether text= is set or selector= is set

        :param selector: css selector string
        :return:
        :rtype:
        """
        return await self.wait_for(text, selector, timeout)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Tab):
            return False

        return other.target == self.target

    def __repr__(self) -> str:
        extra = ""
        if self.target is not None and self.target.url:
            extra = f"[url: {self.target.url}]"
        s = f"<{type(self).__name__} [{self.target_id}] [{self.type_}] {extra}>"
        return s
