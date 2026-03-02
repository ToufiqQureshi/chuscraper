from __future__ import annotations

import base64
import datetime
import logging
import pathlib
import secrets
import typing
import urllib.parse
from typing import TYPE_CHECKING

from ... import cdp
from .base import ElementMixin
from ..config import PathLike

if TYPE_CHECKING:
    from ..connection import ProtocolException

logger = logging.getLogger(__name__)


class ElementMediaMixin(ElementMixin):
    async def screenshot_b64(
        self,
        format: str = "jpeg",
        scale: typing.Optional[typing.Union[int, float]] = 1,
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
        filename: typing.Optional[PathLike] = "auto",
        format: str = "jpeg",
        scale: typing.Optional[typing.Union[int, float]] = 1,
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

    async def flash(self, duration: typing.Union[float, int] = 0.5, retry: Optional[bool] = None) -> None:
        from ..connection import ProtocolException

        if retry is None:
            config = self.tab.browser.config if self.tab.browser else None
            retry = getattr(config, "retry_enabled", False)

        if not self.remote_object:
            try:
                setattr(
                    self,
                    "_remote_object",
                    await self.tab.send(
                        cdp.dom.resolve_node(backend_node_id=self.backend_node_id)
                    ),
                )
            except ProtocolException:
                return
        if not self.remote_object or not self.remote_object.object_id:
            raise ValueError("could not resolve object id for %s" % self)
        pos = await self.get_position()
        if pos is None:
            logger.warning("flash() : could not determine position")
            return

        style = (
            "position:absolute;z-index:99999999;padding:0;margin:0;"
            "left:{:.1f}px; top: {:.1f}px;"
            "opacity:1;"
            "width:16px;height:16px;border-radius:50%;background:red;"
            "animation:show-pointer-ani {:.2f}s ease 1;"
        ).format(
            pos.center[0] - 8,
            pos.center[1] - 8,
            duration,
        )
        script = (
            """
            (targetElement) => {{
                var css = document.styleSheets[0];
                for( let css of [...document.styleSheets]) {{
                    try {{
                        css.insertRule(`
                        @keyframes show-pointer-ani {{
                              0% {{ opacity: 1; transform: scale(2, 2);}}
                              25% {{ transform: scale(5,5) }}
                              50% {{ transform: scale(3, 3);}}
                              75%: {{ transform: scale(2,2) }}
                              100% {{ transform: scale(1, 1); opacity: 0;}}
                        }}`,css.cssRules.length);
                        break;
                    }} catch (e) {{
                        console.log(e)
                    }}
                }};
                var _d = document.createElement('div');
                _d.style = `{0:s}`;
                _d.id = `{1:s}`;
                document.body.insertAdjacentElement('afterBegin', _d);

                setTimeout( () => document.getElementById('{1:s}').remove(), {2:d});
            }}
            """.format(
                style,
                secrets.token_hex(8),
                int(duration * 1000),
            )
            .replace("  ", "")
            .replace("\n", "")
        )

        arguments = [cdp.runtime.CallArgument(object_id=self.remote_object.object_id)]
        try:
            await self.tab.send(
                cdp.runtime.call_function_on(
                    script,
                    object_id=self.remote_object.object_id,
                    arguments=arguments,
                    await_promise=True,
                    user_gesture=True,
                )
            )
        except Exception as e:
            if retry and isinstance(e, ProtocolException) and e.code == -32000:
                logger.debug(f"Retrying flash() on {self.node_name} after stale object_id error")
                setattr(self, '_remote_object', None)
                await self.update()
                return await self.flash(duration=duration, retry=False)
            raise e

    async def highlight_overlay(self) -> None:
        if getattr(self, "_is_highlighted", False):
            del self._is_highlighted
            await self.tab.send(cdp.overlay.hide_highlight())
            await self.tab.send(cdp.dom.disable())
            await self.tab.send(cdp.overlay.disable())
            return
        await self.tab.send(cdp.dom.enable())
        await self.tab.send(cdp.overlay.enable())
        conf = cdp.overlay.HighlightConfig(
            show_info=True, show_extension_lines=True, show_styles=True
        )
        await self.tab.send(
            cdp.overlay.highlight_node(
                highlight_config=conf, backend_node_id=self.backend_node_id
            )
        )
        setattr(self, "_is_highlighted", 1)

    async def record_video(
        self,
        filename: typing.Optional[str] = None,
        folder: typing.Optional[str] = None,
        duration: typing.Optional[typing.Union[int, float]] = None,
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
        await self("pause")
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
        await self("play")
        await self.tab

    async def is_recording(self) -> bool:
        return await self.apply('(vid) => vid["_recording"]')  # type: ignore
