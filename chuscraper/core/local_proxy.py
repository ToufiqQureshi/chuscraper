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
        self.tasks = set()

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
        """Stops the server and cleans up all active tasks."""
        if self.server:
            self.server.close()
            try:
                await asyncio.wait_for(self.server.wait_closed(), timeout=2.0)
            except asyncio.TimeoutError:
                pass
        
        if self.tasks:
            for task in list(self.tasks):
                if not task.done():
                    task.cancel()
            
            # Wait for all tasks to settle with a timeout
            if self.tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*self.tasks, return_exceptions=True), 
                        timeout=2.0
                    )
                except asyncio.TimeoutError:
                    pass
            self.tasks.clear()

    async def handle_client(self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter):
        """Handles a connection from the browser."""
        task = asyncio.current_task()
        if task:
            self.tasks.add(task)
            
        upstream_writer = None
        try:
            # Read first chunk (headers)
            chunk = await asyncio.wait_for(client_reader.read(4096), timeout=5.0)
            if not chunk:
                return

            is_connect = chunk.startswith(b"CONNECT")
            
            # Inject Auth if we have it and it's not already there
            if self.auth_header and b"Proxy-Authorization" not in chunk:
                # Standard HTTP header injection
                # Insertion before the first header terminator
                terminator = b"\r\n\r\n" if b"\r\n\r\n" in chunk else b"\n\n"
                if terminator in chunk:
                    parts = chunk.split(terminator, 1)
                    new_header_data = parts[0] + b"\r\nProxy-Authorization: " + self.auth_header.encode() + terminator + parts[1]
                else:
                    new_header_data = chunk.rstrip() + b"\r\nProxy-Authorization: " + self.auth_header.encode() + b"\r\n\r\n"
            else:
                new_header_data = chunk

            # Connect to upstream proxy
            try:
                upstream_reader, upstream_writer = await asyncio.wait_for(
                    asyncio.open_connection(self.upstream_host, self.upstream_port),
                    timeout=5.0
                )
            except (asyncio.TimeoutError, Exception) as e:
                logger.error(f"Failed to connect to upstream proxy {self.upstream_host}:{self.upstream_port}: {e}")
                return

            # Send modified headers to upstream
            upstream_writer.write(new_header_data)
            await upstream_writer.drain()

            # Pipe the bidirectional data
            # Use FIRST_COMPLETED to ensure cleanup if either side closes
            pipe_client = asyncio.create_task(self.pipe(client_reader, upstream_writer), name="pipe_client")
            pipe_upstream = asyncio.create_task(self.pipe(upstream_reader, client_writer), name="pipe_upstream")
            
            done, pending = await asyncio.wait(
                [pipe_client, pipe_upstream], 
                return_when=asyncio.FIRST_COMPLETED
            )
            for p in pending:
                p.cancel()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"Proxy tunnel error: {e}")
        finally:
            try:
                client_writer.close()
                await client_writer.wait_closed()
            except: pass
            
            if upstream_writer:
                try:
                    upstream_writer.close()
                    await upstream_writer.wait_closed()
                except: pass
                
            if task:
                self.tasks.discard(task)

    async def pipe(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Transfers data between two streams."""
        try:
            while not reader.at_eof():
                # Read with a large buffer, but wait for data
                data = await reader.read(8192)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except Exception:
            pass
        finally:
            try:
                writer.close()
            except: pass

