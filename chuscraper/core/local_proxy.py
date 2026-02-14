"""
Local Proxy Forwarder for Chuscraper.
Implements the "Patchright Architecture" of handling proxy auth outside the browser.

Features:
- Spawns a local TCP server on a free port.
- Intercepts CONNECT/GET requests from Chrome.
- Injects 'Proxy-Authorization' header for the upstream proxy.
- Forwards traffic transparently.
- Eliminates browser auth popups and extension conflicts.
"""

import asyncio
import base64
import logging
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class LocalAuthProxy:
    def __init__(self, upstream_proxy_url: str):
        self.upstream = urlparse(upstream_proxy_url)
        self.upstream_host = self.upstream.hostname
        self.upstream_port = self.upstream.port or 80
        self.auth_header = None
        
        if self.upstream.username and self.upstream.password:
            auth = f"{self.upstream.username}:{self.upstream.password}"
            encoded = base64.b64encode(auth.encode()).decode()
            self.auth_header = f"Basic {encoded}"
            
        self.server = None
        self.local_port = None

    async def start(self) -> int:
        """Starts the local proxy server and returns the port."""
        # Find a free port
        sock = socket.socket()
        sock.bind(('127.0.0.1', 0))
        self.local_port = sock.getsockname()[1]
        sock.close()

        self.server = await asyncio.start_server(
            self.handle_client, '127.0.0.1', self.local_port
        )
        logger.info(f"Local Proxy started on 127.0.0.1:{self.local_port} -> {self.upstream_host}:{self.upstream_port}")
        return self.local_port

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def handle_client(self, client_reader, client_writer):
        """Handles a connection from the browser."""
        try:
            # Connect to upstream proxy
            upstream_reader, upstream_writer = await asyncio.open_connection(
                self.upstream_host, self.upstream_port
            )
            
            # Read the initial request line from client (Chrome)
            # Chrome sends: CONNECT target.com:443 HTTP/1.1
            header_data = b""
            while True:
                line = await client_reader.readline()
                header_data += line
                if line == b'\r\n' or line == b'\n' or not line:
                    break
            
            # Inject Proxy-Authorization
            if self.auth_header:
                # We need to insert the header before the final CRLF
                # header_data ends with \r\n
                headers = header_data.decode()
                lines = headers.splitlines()
                # Remove empty line at end
                if lines and not lines[-1]:
                    lines.pop()
                
                lines.append(f"Proxy-Authorization: {self.auth_header}")
                lines.append("") # Empty line to end headers
                lines.append("")
                
                new_header_data = "\r\n".join(lines).encode()
            else:
                new_header_data = header_data

            # Forward modified headers to upstream
            upstream_writer.write(new_header_data)
            await upstream_writer.drain()

            # Create pipe tasks
            await asyncio.gather(
                self.pipe(client_reader, upstream_writer),
                self.pipe(upstream_reader, client_writer)
            )

        except Exception as e:
            # logger.debug(f"Proxy tunnel error: {e}")
            pass
        finally:
            client_writer.close()

    async def pipe(self, reader, writer):
        try:
            while not reader.at_eof():
                data = await reader.read(4096)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()
