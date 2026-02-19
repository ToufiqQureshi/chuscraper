from __future__ import annotations
from .base import TabMixin
from typing import TYPE_CHECKING, Optional
import base64
import datetime
import pathlib
import urllib.parse
from ... import cdp
from ..config import PathLike
from ..connection import ProtocolException

if TYPE_CHECKING:
    from ..tab import Tab

class ScreenshotMixin(TabMixin):
    async def save_snapshot(self, filename: str = "snapshot.mhtml") -> None:
        """
        Saves a snapshot of the page.
        :param filename: The save path; defaults to "snapshot.mhtml"
        """
        await self.tab.sleep()  # update the target's url
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
        if self.tab.target is None:
            raise ValueError("target is none")

        await self.tab.sleep()  # update the target's url

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
            assert self.tab.target is not None
            parsed = urllib.parse.urlparse(self.tab.target.url)
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

    async def print_to_pdf(self, filename: PathLike, **kwargs) -> pathlib.Path:
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
