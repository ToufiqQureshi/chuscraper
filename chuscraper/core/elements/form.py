from __future__ import annotations
from .base import ElementMixin
from typing import TYPE_CHECKING
from ... import cdp
from ..config import PathLike

if TYPE_CHECKING:
    from ..element import Element

class ElementFormMixin(ElementMixin):
    async def clear_input(self) -> None:
        """clears an input field"""
        await self.apply('function (element) { element.value = "" } ')

    async def clear_input_by_deleting(self) -> None:
        await self.apply(
            """
                async function clearByDeleting(n, d = 50) {
                    n.focus();
                    n.setSelectionRange(0, 0);
                    while (n.value.length > 0) {
                        n.dispatchEvent(
                            new KeyboardEvent("keydown", {
                                key: "Delete",
                                code: "Delete",
                                keyCode: 46,
                                which: 46,
                                bubbles: !0,
                                cancelable: !0,
                            })
                        );
                        n.dispatchEvent(
                            new KeyboardEvent("keypress", {
                                key: "Delete",
                                code: "Delete",
                                keyCode: 46,
                                which: 46,
                                bubbles: !0,
                                cancelable: !0,
                            })
                        );
                         n.dispatchEvent(
                            new InputEvent("beforeinput", {
                                inputType: "deleteContentForward",
                                data: null,
                                bubbles: !0,
                                cancelable: !0,
                            })
                        );
                        n.dispatchEvent(
                            new KeyboardEvent("keyup", {
                                key: "Delete",
                                code: "Delete",
                                keyCode: 46,
                                which: 46,
                                bubbles: !0,
                                cancelable: !0,
                            })
                        );
                        n.value = n.value.slice(1);
                        await new Promise((r) => setTimeout(r, d));
                    }
                    n.dispatchEvent(new Event("input", { bubbles: !0 }));
                }
            """,
            await_promise=True,
        )

    async def send_file(self, *file_paths: PathLike) -> None:
        file_paths_as_str = [str(p) for p in file_paths]
        await self.tab.send(
            cdp.dom.set_file_input_files(
                files=[*file_paths_as_str],
                backend_node_id=self.backend_node_id,
                object_id=self.object_id,
            )
        )

    async def focus(self) -> None:
        await self.apply("(element) => element.focus()")

    async def select_option(self) -> None:
        if self.node_name == "OPTION":
            await self.apply(
                """
                (o) => {
                    o.selected = true ;
                    o.dispatchEvent(new Event('change', {view: window,bubbles: true}))
                }
                """
            )

    async def set_value(self, value: str) -> None:
        await self.tab.send(cdp.dom.set_node_value(node_id=self.node_id, value=value))

    async def set_text(self, value: str) -> None:
        if not self.node_type == 3:
            if self.child_node_count == 1:
                child_node = self.children[0]
                # Assuming child_node is an Element due to mixin structure
                if hasattr(child_node, 'set_text'):
                    await child_node.set_text(value)
                    await self.update()
                    return
            else:
                raise RuntimeError("could only set value of text nodes")
        await self.update()
        await self.tab.send(cdp.dom.set_node_value(node_id=self.node_id, value=value))
