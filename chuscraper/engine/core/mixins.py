from chuscraper.engine.core._types import Any, Dict

class SelectorsGeneration:
    def _general_selection(self: Any, selection: str = "css", full_path: bool = False) -> str:
        if self._is_text_node(self._root):
            return ""
        selectorPath = []
        target = self
        css = selection.lower() == "css"
        while target is not None:
            if target.parent:
                if target.attrib.get("id"):
                    part = f"#{target.attrib['id']}" if css else f"[@id='{target.attrib['id']}']"
                    selectorPath.append(part)
                    if not full_path:
                        return " > ".join(reversed(selectorPath)) if css else "//*" + "/".join(reversed(selectorPath))
                else:
                    part = f"{target.tag}"
                    counter: Dict[str, int] = {}
                    for child in target.parent.children:
                        counter.setdefault(child.tag, 0)
                        counter[child.tag] += 1
                        if child._root == target._root:
                            break
                    if counter[target.tag] > 1:
                        part += f":nth-of-type({counter[target.tag]})" if css else f"[{counter[target.tag]}]"
                selectorPath.append(part)
                target = target.parent
                if target is None or target.tag == "html":
                    return " > ".join(reversed(selectorPath)) if css else "//" + "/".join(reversed(selectorPath))
            else:
                break
        return " > ".join(reversed(selectorPath)) if css else "//" + "/".join(reversed(selectorPath))

    @property
    def generate_css_selector(self: Any) -> str: return self._general_selection()
    @property
    def generate_full_css_selector(self: Any) -> str: return self._general_selection(full_path=True)
    @property
    def generate_xpath_selector(self: Any) -> str: return self._general_selection("xpath")
    @property
    def generate_full_xpath_selector(self: Any) -> str: return self._general_selection("xpath", full_path=True)
