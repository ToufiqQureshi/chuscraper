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
import websockets.exceptions

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
    def target_id(self) -> Optional[cdp.target.TargetID]:
        if self.target and hasattr(self.target, "target_id"):
            tid = self.target.target_id
            if tid is not None and not hasattr(tid, "to_json"):
                return cdp.target.TargetID(str(tid))
            return tid
        return None

    @property
    def type_(self) -> Optional[str]:
        if self.target and hasattr(self.target, "type_"):
            return str(self.target.type_)
        return None

    @property
    def closed(self) -> bool:
        """Robust check for connection state."""
        if not self.websocket:
            return True
        try:
            return self.websocket.closed
        except AttributeError:
            return not getattr(self.websocket, "open", False)

    async def connect(self):
        if self._connecting:
            await self._connected.wait()
            return
        if self.websocket and not self.closed:
            return

        self._connecting = True
        self._connected.clear()

        # Shutdown old connection properly
        if self.websocket:
            ws = self.websocket
            self.websocket = None
            if self.recv_task and not self.recv_task.done():
                self.recv_task.cancel()
            try:
                await asyncio.wait_for(ws.close(), timeout=2.0)
            except:
                pass

        try:
            # Production Stability: Heartbeats to keep connection alive
            self.websocket = await websockets.asyncio.client.connect(
                self.websocket_url,
                max_size=2**28,
                close_timeout=2.0,
                ping_interval=20,
                ping_timeout=20,
            )
            self._connected.set()
            self.recv_task = asyncio.create_task(self._recv_loop())
        except Exception as e:
            logger.debug(f"Failed to connect to {self.websocket_url}: {e}")
            self._connected.set()
            raise
        finally:
            self._connecting = False

    async def _recv_loop(self):
        ws = self.websocket
        if not ws:
            return
        try:
            async for message in ws:
                if isinstance(message, bytes):
                    message = message.decode("utf-8")
                await self._handle_message(str(message))
        except Exception as e:
            logger.debug(f"Connection loop terminated for {self.target_id}: {e}")
        finally:
            if self.websocket == ws:
                self.websocket = None
                self._connected.clear()

    async def _handle_message(self, message: str):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return

        if "id" in data:
            tx_id = data["id"]
            if tx_id in self.mapper:
                tx = self.mapper[tx_id]
                if not tx.future.done():
                    if "error" in data:
                        tx.future.set_exception(ProtocolException(data["error"]))
                    else:
                        tx.future.set_result(data.get("result", {}))
                del self.mapper[tx_id]

        elif "method" in data:
            method = data["method"]
            params = data.get("params", {})
            event_type = cdp.util._event_parsers.get(method)

            if not event_type:
                try:
                    if "." in method:
                        domain_name, event_name = method.split(".", 1)
                        domain_module = getattr(cdp, domain_name.lower(), None)
                        if domain_module:
                            target_name = event_name.lower().replace("_", "")
                            for name, obj in inspect.getmembers(domain_module):
                                if (
                                    inspect.isclass(obj)
                                    and name.lower() == target_name
                                ):
                                    event_type = obj
                                    break
                except Exception:
                    pass

            if event_type:
                event_obj = None
                try:
                    if hasattr(event_type, "from_json"):
                        event_obj = event_type.from_json(params)
                except Exception:
                    pass

                if event_obj is None:
                    event_obj = params

                handlers = self.handlers.get(event_type, []) + self.handlers.get(
                    method, []
                )
                for handler in handlers:
                    try:
                        if inspect.iscoroutinefunction(handler):
                            asyncio.create_task(handler(event_obj))
                        else:
                            handler(event_obj)
                    except Exception as e:
                        logger.debug(f"Error in event handler for {method}: {e}")

    async def send(self, command: Any, session_id: str = None, **kwargs: Any) -> Any:
        # 1. Standardize command data for retries
        is_gen = inspect.isgenerator(command)
        if is_gen:
            try:
                cmd_data = next(command)
                method = cmd_data.get("method")
                params = cmd_data.get("params", {})
            except StopIteration:
                return None
        else:
            method = getattr(command, "method", None)
            if not method and isinstance(command, dict):
                method = command.get("method")
                params = command.get("params", {})
            else:
                params = (
                    getattr(command, "params", {})
                    if hasattr(command, "params")
                    else {}
                )

        if not method:
            raise ValueError(f"Could not determine method from command: {command}")

        # 2. Execute with Production Grade recovery
        max_retries = 3
        result = None
        for attempt in range(max_retries):
            try:
                if self.closed:
                    await self.connect()

                result = await self._raw_send(method, params, session_id)
                break # Success
            except (ConnectionError, websockets.exceptions.ConnectionClosed, OSError) as e:
                is_win_error_64 = False
                if sys.platform == "win32" and isinstance(e, OSError) and getattr(e, "winerror", 0) == 64:
                    is_win_error_64 = True

                if attempt < max_retries - 1 and (is_win_error_64 or isinstance(e, (ConnectionError, websockets.exceptions.ConnectionClosed))):
                    logger.debug(f"Connection lost (Win64: {is_win_error_64}), retrying... {attempt+1}")
                    await self.connect()
                    continue
                raise
            except ProtocolException as e:
                # DOM Agent recovery
                if e.code == -32000 and "DOM agent is not enabled" in e.message and attempt < max_retries - 1:
                    logger.debug("Auto-enabling DOM agent...")
                    try: await self._raw_send("DOM.enable", {}, session_id)
                    except: pass
                    continue
                raise

        # 3. Finalize generator if needed
        if is_gen:
            try:
                command.send(result)
            except StopIteration as e:
                return e.value
        return result

    async def _raw_send(self, method: str, params: dict, session_id: str = None) -> Any:
        final_method = method
        final_params = params

        if session_id:
            final_params = {
                "sessionId": session_id,
                "method": method,
                "params": params,
            }
            final_method = "Target.sendMessageToTarget"

        tx_id = next(self._count)
        tx = Transaction(tx_id, final_method, final_params)
        self.mapper[tx_id] = tx

        payload = {"id": tx_id, "method": final_method, "params": final_params}

        try:
            await self.websocket.send(json.dumps(payload))
        except Exception:
            raise

        try:
            return await tx.future
        except Exception:
            raise

    async def stop(self):
        if self.recv_task:
            self.recv_task.cancel()
        if self.websocket:
            try: await self.websocket.close()
            except: pass
            self.websocket = None

    close = stop
    aclose = stop

    def add_handler(self, event_type: Any, handler: Callable):
        if handler not in self.handlers[event_type]:
            self.handlers[event_type].append(handler)

    def remove_handlers(
        self, event_type: Optional[Any] = None, handler: Optional[Callable] = None
    ):
        if event_type:
            if handler:
                if handler in self.handlers[event_type]:
                    self.handlers[event_type].remove(handler)
            else:
                del self.handlers[event_type]
        elif handler:
            for et in list(self.handlers.keys()):
                if handler in self.handlers[et]:
                    self.handlers[et].remove(handler)
        else:
            self.handlers.clear()
