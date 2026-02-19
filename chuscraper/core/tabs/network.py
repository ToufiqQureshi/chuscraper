from __future__ import annotations
from .base import TabMixin
from typing import TYPE_CHECKING, Dict, Optional, List, Union
import re
import pathlib
import warnings
from ... import cdp
from ..intercept import BaseFetchInterception
from ..expect import RequestExpectation, ResponseExpectation, DownloadExpectation
from ...cdp.fetch import RequestStage
from ...cdp.network import ResourceType
from ..config import PathLike

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

    def expect_request(
        self, url_pattern: Union[str, re.Pattern[str]]
    ) -> RequestExpectation:
        """
        Creates a request expectation for a specific URL pattern.
        :param url_pattern: The URL pattern to match requests.
        :return: A RequestExpectation instance.
        :rtype: RequestExpectation
        """
        return RequestExpectation(self.tab, url_pattern)

    def expect_response(
        self, url_pattern: Union[str, re.Pattern[str]]
    ) -> ResponseExpectation:
        """
        Creates a response expectation for a specific URL pattern.
        :param url_pattern: The URL pattern to match responses.
        :return: A ResponseExpectation instance.
        :rtype: ResponseExpectation
        """
        return ResponseExpectation(self.tab, url_pattern)

    def expect_download(self) -> DownloadExpectation:
        """
        Creates a download expectation for next download.
        :return: A DownloadExpectation instance.
        :rtype: DownloadExpectation
        """
        return DownloadExpectation(self.tab)

    def intercept(
        self,
        url_pattern: str,
        request_stage: RequestStage,
        resource_type: Optional[ResourceType] = None,
        resource_types: Optional[List[ResourceType]] = None,
    ) -> BaseFetchInterception:
        """
        Sets up interception for network requests matching a URL pattern, request stage, and resource type.

        :param url_pattern: URL string or regex pattern to match requests.
        :param request_stage: Stage of the request to intercept (e.g., request, response).
        :param resource_type: Type of resource (e.g., Document, Script, Image).
        :param resource_types: List of resource types to intercept.
        :return: A BaseFetchInterception instance for further configuration or awaiting intercepted requests.
        :rtype: BaseFetchInterception

        Use this to block, modify, or inspect network traffic for specific resources during browser automation.
        """
        return BaseFetchInterception(
            self.tab, url_pattern, request_stage, resource_type, resource_types
        )

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
        self.tab._download_behavior = ["allow", str(path.resolve())]

    async def download_file(
        self, url: str, filename: Optional[PathLike] = None
    ) -> None:
        """
        downloads file by given url.

        :param url: url of the file
        :param filename: the name for the file. if not specified the name is composed from the url file name
        """
        if not self.tab._download_behavior:
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

        body = (await self.tab.query_selector_all("body"))[0]
        await body.update()
        await self.send(
            cdp.runtime.call_function_on(
                code,
                object_id=body.object_id,
                arguments=[cdp.runtime.CallArgument(object_id=body.object_id)],
            )
        )
