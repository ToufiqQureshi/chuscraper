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

import websockets
import websockets.asyncio.client

from .. import cdp
from . import util

if TYPE_CHECKING:
    from chuscraper.core.browser import Browser

T = TypeVar("T")

logger = logging.getLogger("uc.connection")

class ProtocolException(Exception):
    def __init__(self, data: Any):
        self.data = data
        self.message = data.get("message", "Unknown CDP Error") if isinstance(data, dict) else str(data)
        self.code = data.get("code", 0) if isinstance(data, dict) else 0
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
        self._target = target
        self._owner = _owner
        self._count = itertools.count(1)
        self.websocket: websockets.asyncio.client.ClientConnection | None = None
        self.mapper: Dict[int, Transaction] = {}
        self.handlers: Dict[Any, List[Callable]] = collections.defaultdict(list)
        self.recv_task: Optional[asyncio.Task] = None
        self.__dict__.update(**kwargs)

    @property
    def target(self) -> Optional[Any]:
        return self._target

    @target.setter
    def target(self, value: Any):
        self._target = value

    @property
    def target_id(self) -> Optional[str]:
        if self._target and hasattr(self._target, 'target_id'):
            return str(self._target.target_id)
        return None

    @property
    def type_(self) -> Optional[str]:
        if self._target and hasattr(self._target, 'type_'):
            return str(self._target.type_)
        return None

    @property
    def closed(self) -> bool:
        """Robust check for connection state."""
        if not self.websocket: 
            return True
        # websockets.asyncio.client.ClientConnection has no 'closed' but has 'state' or 'protocol.state'
        # Safest way to check for 'open' state:
        return getattr(self.websocket, "closed", True) if hasattr(self.websocket, "closed") else not getattr(self.websocket, "open", False)

    async def connect(self):
        if self.websocket: return
        try:
            self.websocket = await websockets.asyncio.client.connect(
                self.websocket_url, max_size=2**28
            )
            self.recv_task = asyncio.create_task(self._recv_loop())
        except Exception:
            raise

    async def _recv_loop(self):
        try:
            async for message in self.websocket:
                await self._handle_message(str(message))
        except Exception:
            self.websocket = None

    async def _handle_message(self, message: str):
        try:
            data = json.loads(message)
            if "id" in data:
                tx = self.mapper.pop(data["id"], None)
                if tx and not tx.future.done():
                    if "error" in data: tx.future.set_exception(ProtocolException(data["error"]))
                    else: tx.future.set_result(data.get("result", {}))
            elif "method" in data:
                method = data["method"]
                params = data.get("params", {})
                event_class = cdp.util._event_parsers.get(method)
                if event_class:
                    event_obj = event_class.from_json(params)
                    for handler in self.handlers.get(event_class, []):
                        try:
                            if inspect.iscoroutinefunction(handler): asyncio.create_task(handler(event_obj))
                            else: handler(event_obj)
                        except Exception: pass
        except Exception: pass

    async def send(self, command: Any, session_id: str = None, **kwargs: Any) -> Any:
        if not self.websocket: await self.connect()
        if inspect.isgenerator(command):
            cmd_data = next(command)
            method = cmd_data["method"]
            params = cmd_data.get("params", {})
        else:
            method = getattr(command, "method", "Unknown")
            params = command if isinstance(command, dict) else {}
        if session_id:
            params = {"sessionId": session_id, "method": method, "params": params}
            method = "Target.sendMessageToTarget"
        tx_id = next(self._count)
        tx = Transaction(tx_id, method, params)
        self.mapper[tx_id] = tx
        await self.websocket.send(json.dumps(tx.to_json()))
        try:
            result = await tx.future
            if inspect.isgenerator(command): command.send(result)
        except StopIteration as e: return e.value
        except Exception as e: raise e
        return result

    async def stop(self):
        if self.recv_task: self.recv_task.cancel()
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
    close = stop
    def add_handler(self, event_type: Any, handler: Callable):
        self.handlers[event_type].append(handler)
