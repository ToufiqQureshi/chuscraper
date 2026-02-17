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
            # Connect to upstream proxy with timeout
            try:
                upstream_reader, upstream_writer = await asyncio.wait_for(
                    asyncio.open_connection(self.upstream_host, self.upstream_port),
                    timeout=5.0
                )
            except (asyncio.TimeoutError, Exception) as e:
                logger.error(f"Failed to connect to upstream proxy {self.upstream_host}:{self.upstream_port}: {e}")
                return

            # Read the initial request line from client (Chrome)
            # Chrome sends: CONNECT target.com:443 HTTP/1.1
            header_data = b""
            is_connect = False
            
            try:
                while True:
                    # Use timeout to prevent vertical deadlock
                    line = await asyncio.wait_for(client_reader.readline(), timeout=5.0)
                    if not line:
                        break
                    
                    if not header_data:
                        if line.startswith(b"CONNECT"):
                            is_connect = True
                    
                    header_data += line
                    if line == b'\r\n' or line == b'\n':
                        break
            except asyncio.TimeoutError:
                logger.debug("Timeout reading headers from client")
                return

            # If it's a CONNECT request, we need to respond to the client (Chrome)
            # that the tunnel is established AFTER we successfully connected to upstream.
            if is_connect:
                # We forward the CONNECT to upstream if it's a proxy 
                # (some proxies expect CONNECT, others expect raw tunnel if passed via --proxy-server)
                # For basic HTTP proxies with auth, we send the CONNECT + Auth.
                
                headers = header_data.decode(errors='ignore')
                lines = headers.splitlines()
                
                if self.auth_header:
                    # Inject Proxy-Authorization
                    if lines and not any("Proxy-Authorization" in l for l in lines):
                        lines.append(f"Proxy-Authorization: {self.auth_header}")
                
                # Reconstruct headers
                new_header_data = ("\r\n".join(lines) + "\r\n\r\n").encode()
                upstream_writer.write(new_header_data)
                await upstream_writer.drain()
                
                # IMPORTANT: We MUST tell Chrome we are ready if we are the "Final" hop it sees.
                # Chrome expects "HTTP/1.1 200 Connection Established"
                client_writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                await client_writer.drain()
                
            else:
                # Standard GET/POST request (Non-HTTPS or explicit proxy)
                if self.auth_header:
                    headers = header_data.decode(errors='ignore')
                    lines = headers.splitlines()
                    if lines and not any("Proxy-Authorization" in l for l in lines):
                        lines.append(f"Proxy-Authorization: {self.auth_header}")
                    new_header_data = ("\r\n".join(lines) + "\r\n\r\n").encode()
                else:
                    new_header_data = header_data

                upstream_writer.write(new_header_data)
                await upstream_writer.drain()

            # Create pipe tasks
            await asyncio.gather(
                self.pipe(client_reader, upstream_writer),
                self.pipe(upstream_reader, client_writer),
                return_exceptions=True
            )

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

