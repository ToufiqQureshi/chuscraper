from __future__ import annotations
from .base import TabMixin
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..tab import Tab

class EvaluationMixin(TabMixin):
    async def evaluate(self, expression: str, await_promise: bool = True) -> Any:
        """Executes JavaScript in the page."""
        res = await self.send(self.cdp.runtime.evaluate(
            expression, 
            return_by_value=True, 
            await_promise=await_promise,
            user_gesture=True
        ))
        return res[0].value if res and res[0] else None

    async def call(self, function: str, *args: Any):
        """Calls a global JS function with arguments."""
        # CDP runtime.call_function_on with global object id?
        # Simpler: evaluate string with injected args
        pass
