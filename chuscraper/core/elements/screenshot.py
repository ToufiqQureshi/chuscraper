from __future__ import annotations
from .base import ElementMixin
from typing import TYPE_CHECKING, Optional, Union
import base64
import datetime
import pathlib
import urllib.parse
from ... import cdp
from ..config import PathLike

if TYPE_CHECKING:
    from ..element import Element

class ElementScreenshotMixin(ElementMixin):
    async def screenshot_b64(
        self,
        format: str = "jpeg",
        scale: Optional[Union[int, float]] = 1,
    ) -> str:
        pos = await self.get_position()
        if not pos:
            raise RuntimeError(
                "could not determine position of element. probably because it's not in view, or hidden"
            )
        viewport = pos.to_viewport(float(scale if scale else 1))
        await self.tab.sleep()

        data = await self.tab.send(
            cdp.page.capture_screenshot(
                format, clip=viewport, capture_beyond_viewport=True
            )
        )

        if not data:
            from ..connection import ProtocolException

            raise ProtocolException(
                "could not take screenshot. most possible cause is the page has not finished loading yet."
            )

        return data

    async def save_screenshot(
        self,
        filename: Optional[PathLike] = "auto",
        format: str = "jpeg",
        scale: Optional[Union[int, float]] = 1,
    ) -> str:
        await self.tab.sleep()

        if not filename or filename == "auto":
            parsed = urllib.parse.urlparse(self.tab.target.url)  # type: ignore
            parts = parsed.path.split("/")
            last_part = parts[-1]
            last_part = last_part.rsplit("?", 1)[0]
            dt_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            candidate = f"{parsed.hostname}__{last_part}_{dt_str}"
            ext = ""
            if format.lower() in ["jpg", "jpeg"]:
                ext = ".jpg"
            elif format.lower() in ["png"]:
                ext = ".png"
            path = pathlib.Path(candidate + ext)
        else:
            path = pathlib.Path(filename)

        path.parent.mkdir(parents=True, exist_ok=True)

        data = await self.screenshot_b64(format, scale)

        data_bytes = base64.b64decode(data)
        path.write_bytes(data_bytes)
        return str(path)

    async def record_video(
        self,
        filename: Optional[str] = None,
        folder: Optional[str] = None,
        duration: Optional[Union[int, float]] = None,
    ) -> None:
        if self.node_name != "VIDEO":
            raise RuntimeError(
                "record_video can only be called on html5 video elements"
            )
        if not folder:
            directory_path = pathlib.Path.cwd() / "downloads"
        else:
            directory_path = pathlib.Path(folder)

        directory_path.mkdir(exist_ok=True)
        await self.tab.send(
            cdp.browser.set_download_behavior(
                "allow", download_path=str(directory_path)
            )
        )
        await self.apply("(vid) => vid.pause()")
        await self.apply(
            """
            function extractVid(vid) {{

                      var duration = {duration:.1f};
                      var stream = vid.captureStream();
                      var mr = new MediaRecorder(stream, {{audio:true, video:true}})
                      mr.ondataavailable  = function(e) {{
                          vid['_recording'] = false
                          var blob = e.data;
                          f = new File([blob], {{name: {filename}, type:'octet/stream'}});
                          var objectUrl = URL.createObjectURL(f);
                          var link = document.createElement('a');
                          link.setAttribute('href', objectUrl)
                          link.setAttribute('download', {filename})
                          link.style.display = 'none'

                          document.body.appendChild(link)

                          link.click()

                          document.body.removeChild(link)
                       }}

                       mr.start()
                       vid.addEventListener('ended' , (e) => mr.stop())
                       vid.addEventListener('pause' , (e) => mr.stop())
                       vid.addEventListener('abort', (e) => mr.stop())


                       if ( duration ) {{
                            setTimeout(() => {{ vid.pause(); vid.play() }}, duration);
                       }}
                       vid['_recording'] = true
                  ;}}

            """.format(
                filename=f'"{filename}"' if filename else 'document.title + ".mp4"',
                duration=int(duration * 1000) if duration else 0,
            )
        )
        await self.apply("(vid) => vid.play()")
        await self.tab

    async def is_recording(self) -> bool:
        return await self.apply('(vid) => vid["_recording"]')  # type: ignore
