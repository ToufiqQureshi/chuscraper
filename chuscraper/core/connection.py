from __future__ import annotations

import asyncio
import collections
import inspect
import itertools
import json
import logging
import sys
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Generator,
    Optional,
    TypeVar,
    Union,
    Dict,
    List,
)

import websockets.asyncio.client

from .. import cdp
from . import util

if TYPE_CHECKING:
    from chuscraper.core.browser import Browser

T = TypeVar("T")

logger = logging.getLogger("uc.connection")


class ProtocolException(Exception):
    def __init__(self, data: Any):
        if isinstance(data, dict):
            self.message = data.get("message", "Unknown CDP Error")
            self.code = data.get("code", 0)
        else:
            self.message = str(data)
            self.code = 0
        self.data = data
        super().__init__(self.message)

    def __str__(self):
        return f"CDP Error {self.code}: {self.message}"


class Transaction:
    def __init__(self, id: int, method: str, params: dict):
        self.id = id
        self.method = method
        self.params = params
        self.future = asyncio.get_running_loop().create_future()

    def to_json(self):
        return {"id": self.id, "method": self.method, "params": self.params}


class Connection:
    def __init__(
        self,
        websocket_url: str,
        target: Optional[Any] = None,
        _owner: Optional[Any] = None,
        **kwargs: Any,
    ):
        self.websocket_url = websocket_url
        self.target = target
        self._owner = _owner
        self._count = itertools.count(1)
        self.websocket: websockets.asyncio.client.ClientConnection | None = None
        self.mapper: Dict[int, Transaction] = {}
        self.handlers: Dict[Any, List[Callable]] = collections.defaultdict(list)
        self.recv_task: Optional[asyncio.Task] = None
        self._connected = asyncio.Event()
        self._connecting = False
        self.__dict__.update(**kwargs)

    @property
    def target_id(self) -> Optional[str]:
        if self.target and hasattr(self.target, 'target_id'):
            return str(self.target.target_id)
        return None

    @property
    def type_(self) -> Optional[str]:
        if self.target and hasattr(self.target, 'type_'):
            return str(self.target.type_)
        return None

    @property
    def closed(self) -> bool:
        """Robust check for connection state."""
        if not self.websocket:
            return True
        # Check if the connection is closed
        try:
            return self.websocket.closed
        except AttributeError:
            # Fallback for older websockets versions or different interfaces
            return not getattr(self.websocket, "open", False)

    async def connect(self):
        if self._connecting:
            await self._connected.wait()
            return
        if self.websocket and not self.closed:
            return

        self._connecting = True
        self._connected.clear()

        if self.websocket:
            ws = self.websocket
            self.websocket = None
            try:
                 # Forcefully close to free the file descriptor
                 await asyncio.wait_for(ws.close(), timeout=1.0)
            except: pass
        try:
            self.websocket = await websockets.asyncio.client.connect(
                self.websocket_url,
                max_size=2**28,
                close_timeout=1.0
            )
            self._connected.set()
            if self.recv_task and not self.recv_task.done():
                self.recv_task.cancel()
            self.recv_task = asyncio.create_task(self._recv_loop())
        except Exception as e:
            logger.error(f"Failed to connect to {self.websocket_url}: {e}")
            self._connected.set() # Release waiters even on failure
            raise
        finally:
            self._connecting = False

    async def _recv_loop(self):
        try:
            async for message in self.websocket:
                # Handle both text and bytes (though CDP is usually text/JSON)
                if isinstance(message, bytes):
                    message = message.decode("utf-8")
                await self._handle_message(str(message))
        except Exception as e:
            logger.debug(f"Connection loop terminated: {e}")
        finally:
            self.websocket = None
            self._connected.clear()

    async def _handle_message(self, message: str):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            logger.warning(f"Received invalid JSON: {message}")
            return

        # Handle Responses (IDs)
        if "id" in data:
            tx_id = data["id"]
            if tx_id in self.mapper:
                tx = self.mapper[tx_id]
                if not tx.future.done():
                    if "error" in data:
                        tx.future.set_exception(ProtocolException(data["error"]))
                    else:
                        tx.future.set_result(data.get("result", {}))
                # Clean up finished transaction
                del self.mapper[tx_id]

        # Handle Events (Methods)
        elif "method" in data:
            method = data["method"]
            params = data.get("params", {})

            # Find the CDP event class for this method
            # This relies on cdp.util._event_parsers.get or manual lookup
            event_type = None

            # 1. Try cdp utility map if available (it might be sparse in some versions)
            event_class = cdp.util._event_parsers.get(method)
            if event_class:
                event_type = event_class
            else:
                # 2. Heuristic lookup: "Network.requestWillBeSent" -> cdp.network.RequestWillBeSent
                try:
                    if "." in method:
                        domain_name, event_name = method.split(".", 1)
                        domain_module = getattr(cdp, domain_name.lower(), None)
                        if domain_module:
                            # Normalize event name (e.g. requestWillBeSent -> RequestWillBeSent)
                            # But python classes are typically PascalCase
                            # We search for case-insensitive match
                            target_name = event_name.lower().replace("_", "")
                            for name, obj in inspect.getmembers(domain_module):
                                if inspect.isclass(obj) and name.lower() == target_name:
                                    event_type = obj
                                    break
                except Exception:
                    pass

            # Fire handlers
            if event_type:
                # Parse the event
                try:
                    event_obj = event_type.from_json(params)
                except Exception:
                    event_obj = params

                handlers = self.handlers.get(event_type, [])
                for handler in handlers:
                    try:
                        if inspect.iscoroutinefunction(handler):
                            asyncio.create_task(handler(event_obj))
                        else:
                            handler(event_obj)
                    except Exception as e:
                        logger.error(f"Error in event handler for {method}: {e}")

            # Also fire generic handlers for the module/domain if registered?
            # (Skipped for now to match original behavior logic)

    async def send(self, command: Any, session_id: str = None, **kwargs: Any) -> Any:
        if self.closed:
            await self.connect()

        # Handle Generator-based commands (cdp module pattern)
        if inspect.isgenerator(command):
            try:
                cmd_data = next(command)
            except StopIteration:
                return None
            method = cmd_data.get("method")
            params = cmd_data.get("params", {})
        else:
            # Handle direct dict or object commands
            method = getattr(command, "method", None)
            if not method and isinstance(command, dict):
                 method = command.get("method")
                 params = command.get("params", {})
            else:
                 params = getattr(command, "params", {}) if hasattr(command, "params") else {}

        if not method:
             raise ValueError(f"Could not determine method from command: {command}")

        final_method = method
        final_params = params

        if session_id:
            final_params = {"sessionId": session_id, "method": method, "params": params}
            final_method = "Target.sendMessageToTarget"

        tx_id = next(self._count)
        tx = Transaction(tx_id, final_method, final_params)
        self.mapper[tx_id] = tx

        payload = {"id": tx_id, "method": final_method, "params": final_params}

        try:
            await self.websocket.send(json.dumps(payload))
        except Exception:
             raise

        # Wait for response
        try:
            result = await tx.future
            # If it was a generator, feed the result back (CDP pattern)
            if inspect.isgenerator(command):
                try:
                    command.send(result)
                except StopIteration as e:
                    return e.value
            return result
        except Exception as e:
            raise e

    async def stop(self):
        if self.recv_task:
            self.recv_task.cancel()
            try:
                await self.recv_task
            except asyncio.CancelledError:
                pass

        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    close = stop
    aclose = stop

    def add_handler(self, event_type: Any, handler: Callable):
        """
        Register a handler for a specific CDP event type.
        """
        if handler not in self.handlers[event_type]:
            self.handlers[event_type].append(handler)

    def remove_handlers(self, event_type: Optional[Any] = None, handler: Optional[Callable] = None):
        """
        Remove handlers.
        If event_type is provided, removes handlers for that type.
        If handler is provided, removes that specific handler.
        If both, removes that handler from that type.
        """
        if event_type:
            if handler:
                if handler in self.handlers[event_type]:
                    self.handlers[event_type].remove(handler)
            else:
                del self.handlers[event_type]
        elif handler:
            # Remove this handler from ALL events
            for et in list(self.handlers.keys()):
                if handler in self.handlers[et]:
                    self.handlers[et].remove(handler)
        else:
            # Clear all
            self.handlers.clear()
