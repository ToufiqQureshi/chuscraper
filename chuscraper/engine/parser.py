from pathlib import Path
from inspect import signature
from urllib.parse import urljoin
from difflib import SequenceMatcher
from re import Pattern as re_Pattern

from lxml.html import HtmlElement, HTMLParser
from cssselect import SelectorError, SelectorSyntaxError, parse as split_selectors
from lxml.etree import (
    XPath,
    tostring,
    fromstring,
    XPathError,
    XPathEvalError,
    _ElementUnicodeResult,
)

from chuscraper.engine.core._types import (
    Any, Set, Dict, cast, List, Tuple, Union, TypeVar, Pattern, Callable, Literal, Optional, Iterable, overload, Generator, SupportsIndex, TYPE_CHECKING
)
from chuscraper.engine.core.custom_types import AttributesHandler, TextHandler, TextHandlers
from chuscraper.engine.core.mixins import SelectorsGeneration
from chuscraper.engine.core.storage import SQLiteStorageSystem, StorageSystemMixin, _StorageTools
from chuscraper.engine.core.translator import css_to_xpath as _css_to_xpath
from chuscraper.engine.core.utils import clean_spaces, flatten, html_forbidden, log

__DEFAULT_DB_FILE__ = str(Path(__file__).parent / "elements_storage.db")
_whitelisted = {"class_": "class", "for_": "for"}
_T = TypeVar("_T")
_find_all_elements = XPath(".//*")
_find_all_elements_with_spaces = XPath(".//*[normalize-space(text())]")

class Selector(SelectorsGeneration):
    __slots__ = ("url", "encoding", "__adaptive_enabled", "_root", "_storage", "__keep_comments", "__huge_tree_enabled", "__attributes", "__text", "__tag", "__keep_cdata", "_raw_body")

    def __init__(self, content: Optional[str | bytes] = None, url: str = "", encoding: str = "utf-8", huge_tree: bool = True, root: Optional[HtmlElement] = None, keep_comments: Optional[bool] = False, keep_cdata: Optional[bool] = False, adaptive: Optional[bool] = False, _storage: Optional[StorageSystemMixin] = None, storage: Any = SQLiteStorageSystem, storage_args: Optional[Dict] = None, **_):
        if root is None and content is None: raise ValueError("Selector class needs HTML content, or root arguments to work")
        self.url = url
        self._raw_body: str | bytes = ""
        self.encoding = encoding
        self.__keep_cdata = keep_cdata
        self.__huge_tree_enabled = huge_tree
        self.__keep_comments = keep_comments
        self.__text: Optional[TextHandler] = None
        self.__attributes: Optional[AttributesHandler] = None
        self.__tag: Optional[str] = None
        self._storage: Optional[StorageSystemMixin] = None
        if root is None:
            body: str | bytes
            if isinstance(content, str): body = content.strip().replace("\x00", "") or "<html/>"
            elif isinstance(content, bytes): body = content.replace(b"\x00", b"")
            else: raise TypeError(f"content must be str or bytes")
            _parser_kwargs = dict(recover=True, remove_blank_text=True, remove_comments=(not keep_comments), encoding=encoding, compact=True, huge_tree=huge_tree, default_doctype=True, strip_cdata=(not keep_cdata))
            parser = HTMLParser(**_parser_kwargs)
            self._root = cast(HtmlElement, fromstring(body or "<html/>", parser=parser, base_url=url or ""))
            self._raw_body = content
        else:
            self._root = cast(HtmlElement, root)
            if self._is_text_node(root):
                self.__adaptive_enabled = False
                return
        self.__adaptive_enabled = bool(adaptive)
        if self.__adaptive_enabled:
            if _storage is not None: self._storage = _storage
            else:
                if not storage_args: storage_args = {"storage_file": __DEFAULT_DB_FILE__, "url": url}
                if not hasattr(storage, "__wrapped__"): raise ValueError("Storage class must be wrapped with lru_cache")
                self._storage = storage(**storage_args)

    def __getitem__(self, key: str) -> TextHandler:
        if self._is_text_node(self._root): raise TypeError("Text nodes do not have attributes")
        return self.attrib[key]
    def __contains__(self, key: str) -> bool:
        if self._is_text_node(self._root): return False
        return key in self.attrib
    @staticmethod
    def _is_text_node(element: HtmlElement | _ElementUnicodeResult) -> bool: return issubclass(type(element), _ElementUnicodeResult)
    def __element_convertor(self, element: HtmlElement | _ElementUnicodeResult) -> "Selector":
        return Selector(root=element, url=self.url, encoding=self.encoding, adaptive=self.__adaptive_enabled, _storage=self._storage, keep_comments=self.__keep_comments, keep_cdata=self.__keep_cdata, huge_tree=self.__huge_tree_enabled)
    def __elements_convertor(self, elements: List[HtmlElement | _ElementUnicodeResult]) -> "Selectors":
        return Selectors(self.__element_convertor(el) for el in elements)
    def __handle_elements(self, result: List[HtmlElement | _ElementUnicodeResult]) -> "Selectors":
        return self.__elements_convertor(result) if result else Selectors()
    def __getstate__(self) -> Any: raise TypeError("Can't pickle Selector objects")
    @property
    def tag(self) -> str:
        if self._is_text_node(self._root): return "#text"
        if not self.__tag: self.__tag = str(self._root.tag)
        return self.__tag or ""
    @property
    def text(self) -> TextHandler:
        if self._is_text_node(self._root): return TextHandler(str(self._root))
        if self.__text is None: self.__text = TextHandler(self._root.text or "")
        return self.__text
    def get_all_text(self, separator: str = "\n", strip: bool = False, ignore_tags: Tuple = ("script", "style"), valid_values: bool = True) -> TextHandler:
        if self._is_text_node(self._root): return TextHandler(str(self._root))
        ignored_elements: set[Any] = set()
        if ignore_tags:
            for element in self._root.iter(*ignore_tags):
                ignored_elements.add(element)
                ignored_elements.update(cast(list, _find_all_elements(element)))
        _all_strings = []
        for node in self._root.iter():
            if node not in ignored_elements:
                text = node.text
                if text and isinstance(text, str):
                    processed_text = text.strip() if strip else text
                    if not valid_values or processed_text.strip(): _all_strings.append(processed_text)
        return cast(TextHandler, TextHandler(separator).join(_all_strings))
    def urljoin(self, relative_url: str) -> str: return urljoin(self.url, relative_url)
    @property
    def attrib(self) -> AttributesHandler:
        if self._is_text_node(self._root): return AttributesHandler({})
        if not self.__attributes: self.__attributes = AttributesHandler(self._root.attrib)
        return self.__attributes
    @property
    def html_content(self) -> TextHandler:
        if self._is_text_node(self._root): return TextHandler(str(self._root))
        content = tostring(self._root, encoding=self.encoding, method="html", with_tail=False)
        if isinstance(content, bytes): content = content.strip().decode(self.encoding)
        return TextHandler(content)
    @property
    def body(self) -> str | bytes: return self._raw_body if not self._is_text_node(self._root) else ""
    def prettify(self) -> TextHandler:
        if self._is_text_node(self._root): return TextHandler(str(self._root))
        content = tostring(self._root, encoding=self.encoding, pretty_print=True, method="html", with_tail=False)
        if isinstance(content, bytes): content = content.strip().decode(self.encoding)
        return TextHandler(content)
    def has_class(self, class_name: str) -> bool: return class_name in self._root.classes if not self._is_text_node(self._root) else False
    @property
    def parent(self) -> Optional["Selector"]:
        _parent = self._root.getparent()
        return self.__element_convertor(_parent) if _parent is not None else None
    @property
    def below_elements(self) -> "Selectors":
        if self._is_text_node(self._root): return Selectors()
        below = cast(List, _find_all_elements(self._root))
        return self.__elements_convertor(below) if below is not None else Selectors()
    @property
    def children(self) -> "Selectors":
        if self._is_text_node(self._root): return Selectors()
        return Selectors(self.__element_convertor(child) for child in self._root.iterchildren() if not isinstance(child, html_forbidden))
    @property
    def siblings(self) -> "Selectors":
        if self.parent: return Selectors(child for child in self.parent.children if child._root != self._root)
        return Selectors()
    def iterancestors(self) -> Generator["Selector", None, None]:
        if self._is_text_node(self._root): return
        for ancestor in self._root.iterancestors(): yield self.__element_convertor(ancestor)
    def find_ancestor(self, func: Callable[["Selector"], bool]) -> Optional["Selector"]:
        for ancestor in self.iterancestors():
            if func(ancestor): return ancestor
        return None
    @property
    def path(self) -> "Selectors": return Selectors(list(self.iterancestors()))
    @property
    def next(self) -> Optional["Selector"]:
        if self._is_text_node(self._root): return None
        next_element = self._root.getnext()
        while next_element is not None and isinstance(next_element, html_forbidden): next_element = next_element.getnext()
        return self.__element_convertor(next_element) if next_element is not None else None
    @property
    def previous(self) -> Optional["Selector"]:
        if self._is_text_node(self._root): return None
        prev_element = self._root.getprevious()
        while prev_element is not None and isinstance(prev_element, html_forbidden): prev_element = prev_element.getprevious()
        return self.__element_convertor(prev_element) if prev_element is not None else None
    def get(self) -> TextHandler: return TextHandler(str(self._root)) if self._is_text_node(self._root) else self.html_content
    def getall(self) -> TextHandlers: return TextHandlers([self.get()])
    extract = getall
    extract_first = get
    def __str__(self) -> str: return str(self._root) if self._is_text_node(self._root) else str(self.html_content)
    def __repr__(self) -> str:
        limit = 40
        if self._is_text_node(self._root):
            text = str(self._root)
            return f"<text='{text[:limit].strip() + '...' if len(text) > limit else text}'>"
        content = clean_spaces(self.html_content)
        data = f"<data='{content[:limit].strip() + '...' if len(content) > limit else content}'"
        if self.parent:
            parent_content = clean_spaces(self.parent.html_content)
            data += f" parent='{parent_content[:limit].strip() + '...' if len(parent_content) > limit else parent_content}'"
        return data + ">"
    @overload
    def relocate(self, element: Union[Dict, HtmlElement, "Selector"], percentage: int, selector_type: Literal[True]) -> "Selectors": ...
    @overload
    def relocate(self, element: Union[Dict, HtmlElement, "Selector"], percentage: int, selector_type: Literal[False] = False) -> List[HtmlElement]: ...
    def relocate(self, element: Union[Dict, HtmlElement, "Selector"], percentage: int = 0, selector_type: bool = False) -> Union[List[HtmlElement], "Selectors"]:
        score_table: Dict[float, List[Any]] = {}
        if isinstance(element, self.__class__): element = element._root
        if issubclass(type(element), HtmlElement): element = _StorageTools.element_to_dict(element)
        for node in cast(List, _find_all_elements(self._root)):
            score = self.__calculate_similarity_score(cast(Dict, element), node)
            score_table.setdefault(score, []).append(node)
        if score_table:
            highest = max(score_table.keys())
            if score_table[highest] and highest >= percentage:
                return self.__elements_convertor(score_table[highest]) if selector_type else score_table[highest]
        return []
    def css(self, selector: str, identifier: str = "", adaptive: bool = False, auto_save: bool = False, percentage: int = 0) -> "Selectors":
        if self._is_text_node(self._root): return Selectors()
        try:
            if not self.__adaptive_enabled or "," not in selector:
                return self.xpath(_css_to_xpath(selector), identifier or selector, adaptive, auto_save, percentage)
            results = Selectors()
            for single in split_selectors(selector):
                results += self.xpath(_css_to_xpath(single.canonical()), identifier or single.canonical(), adaptive, auto_save, percentage)
            return Selectors(results)
        except (SelectorError, SelectorSyntaxError) as e: raise SelectorSyntaxError(f"Invalid CSS selector '{selector}': {str(e)}") from e
    def xpath(self, selector: str, identifier: str = "", adaptive: bool = False, auto_save: bool = False, percentage: int = 0, **kwargs: Any) -> "Selectors":
        if self._is_text_node(self._root): return Selectors()
        try:
            if elements := self._root.xpath(selector, **kwargs):
                if self.__adaptive_enabled and auto_save: self.save(elements[0], identifier or selector)
                return self.__handle_elements(elements)
            elif self.__adaptive_enabled and adaptive:
                if element_data := self.retrieve(identifier or selector):
                    elements = self.relocate(element_data, percentage)
                    if elements and auto_save: self.save(elements[0], identifier or selector)
                return self.__handle_elements(elements)
            return self.__handle_elements([])
        except (SelectorError, SelectorSyntaxError, XPathError, XPathEvalError) as e: raise SelectorSyntaxError(f"Invalid XPath selector: {selector}") from e
    def find_all(self, *args: str | Iterable[str] | Pattern | Callable | Dict[str, str], **kwargs: str) -> "Selectors":
        if self._is_text_node(self._root): return Selectors()
        if not args and not kwargs: raise TypeError("Filter needed")
        attributes, tags, patterns, functions, selectors = {}, set(), set(), [], []
        for arg in args:
            if isinstance(arg, str): tags.add(arg)
            elif type(arg) in (list, tuple, set): tags.update(set(arg))
            elif isinstance(arg, dict): attributes.update(arg)
            elif isinstance(arg, re_Pattern): patterns.add(arg)
            elif callable(arg): functions.append(arg)
        for k, v in kwargs.items(): attributes[_whitelisted.get(k, k)] = v
        tags = tags or set("*")
        for tag in tags:
            selector = tag
            for k, v in attributes.items(): selector += '[{}="{}"]'.format(k, v.replace('"', r"\""))
            if selector != "*": selectors.append(selector)
        if selectors:
            results = cast(Selectors, self.css(", ".join(selectors)))
            for p in patterns: results = results.filter(lambda e: e.text.re(p, check_match=True))
            for f in functions: results = results.filter(f)
        else:
            results = self.below_elements
            for p in patterns: results = results.filter(lambda e: e.text.re(p, check_match=True))
            for f in functions: results = results.filter(f)
        return results
    def find(self, *args, **kwargs) -> Optional["Selector"]:
        for element in self.find_all(*args, **kwargs): return element
        return None
    def __calculate_similarity_score(self, original: Dict, candidate: HtmlElement) -> float:
        score, checks = 0, 1
        data = _StorageTools.element_to_dict(candidate)
        score += 1 if original["tag"] == data["tag"] else 0
        if original["text"]:
            score += SequenceMatcher(None, original["text"], data.get("text") or "").ratio()
            checks += 1
        score += self.__calculate_dict_diff(original["attributes"], data["attributes"])
        checks += 1
        for attrib in ("class", "id", "href", "src"):
            if original["attributes"].get(attrib):
                score += SequenceMatcher(None, original["attributes"][attrib], data["attributes"].get(attrib) or "").ratio()
                checks += 1
        score += SequenceMatcher(None, original["path"], data["path"]).ratio()
        checks += 1
        if original.get("parent_name") and data.get("parent_name"):
            score += SequenceMatcher(None, original["parent_name"], data.get("parent_name") or "").ratio()
            checks += 1
            score += self.__calculate_dict_diff(original["parent_attribs"], data.get("parent_attribs") or {})
            checks += 1
            if original["parent_text"]:
                score += SequenceMatcher(None, original["parent_text"], data.get("parent_text") or "").ratio()
                checks += 1
        if original.get("siblings"):
            score += SequenceMatcher(None, original["siblings"], data.get("siblings") or []).ratio()
            checks += 1
        return round((score / checks) * 100, 2)
    @staticmethod
    def __calculate_dict_diff(dict1: Dict, dict2: Dict) -> float:
        score = SequenceMatcher(None, tuple(dict1.keys()), tuple(dict2.keys())).ratio() * 0.5
        score += SequenceMatcher(None, tuple(dict1.values()), tuple(dict2.values())).ratio() * 0.5
        return score
    def save(self, element, identifier: str) -> None:
        if self.__adaptive_enabled and self._storage:
            target = element._root if isinstance(element, self.__class__) else element
            if self._is_text_node(target): target = target.getparent()
            self._storage.save(target, identifier)
        else: raise RuntimeError("Adaptive disabled")
    def retrieve(self, identifier: str) -> Optional[Dict[str, Any]]:
        if self.__adaptive_enabled and self._storage: return self._storage.retrieve(identifier)
        raise RuntimeError("Adaptive disabled")
    def json(self) -> Dict:
        if self._is_text_node(self._root): return TextHandler(str(self._root)).json()
        if self._raw_body:
            body = self._raw_body.decode() if isinstance(self._raw_body, bytes) else self._raw_body
            return TextHandler(body).json()
        return self.text.json() if self.text else self.get_all_text(strip=True).json()
    def re(self, regex, replace_entities=True, clean_match=False, case_sensitive=True): return self.text.re(regex, replace_entities, clean_match, case_sensitive)
    def re_first(self, regex, default=None, replace_entities=True, clean_match=False, case_sensitive=True): return self.text.re_first(regex, default, replace_entities, clean_match, case_sensitive)
    def find_similar(self, similarity_threshold=0.2, ignore_attributes=("href", "src"), match_text=False) -> "Selectors":
        if self._is_text_node(self._root): return Selectors()
        root = self._root
        similar_elements = []
        current_depth = len(list(root.iterancestors()))
        target_attrs = {k: v for k, v in root.attrib.items() if k not in ignore_attributes} if ignore_attributes else root.attrib
        path_parts = [self.tag]
        if (parent := root.getparent()) is not None:
            path_parts.insert(0, parent.tag)
            if (grandparent := parent.getparent()) is not None: path_parts.insert(0, grandparent.tag)
        xpath_path = "//{}".format("/".join(path_parts))
        potential_matches = root.xpath(f"{xpath_path}[count(ancestor::*) = {current_depth}]")
        for p in potential_matches:
            if p != root:
                candidate_attrs = {k: v for k, v in p.attrib.items() if k not in ignore_attributes} if ignore_attributes else p.attrib
                score, checks = 0, 0
                if target_attrs:
                    score += sum(SequenceMatcher(None, v, candidate_attrs.get(k, "")).ratio() for k, v in target_attrs.items())
                    checks += len(candidate_attrs)
                elif not candidate_attrs: score, checks = 1, 1
                if match_text:
                    score += SequenceMatcher(None, clean_spaces(root.text or ""), clean_spaces(p.text or "")).ratio()
                    checks += 1
                if checks and round(score / checks, 2) >= similarity_threshold: similar_elements.append(p)
        return Selectors(map(self.__element_convertor, similar_elements))
    @overload
    def find_by_text(self, text: str, first_match: Literal[True] = ..., partial: bool = ..., case_sensitive: bool = ..., clean_match: bool = ...) -> "Selector": ...
    @overload
    def find_by_text(self, text: str, first_match: Literal[False], partial: bool = ..., case_sensitive: bool = ..., clean_match: bool = ...) -> "Selectors": ...
    def find_by_text(self, text: str, first_match: bool = True, partial: bool = False, case_sensitive: bool = False, clean_match: bool = True) -> Union["Selectors", "Selector"]:
        if self._is_text_node(self._root): return Selectors()
        results, search_text = Selectors(), text if case_sensitive else text.lower()
        possible = cast(List, _find_all_elements_with_spaces(self._root))
        if possible:
            for node in self.__elements_convertor(possible):
                nt = node.text
                if clean_match: nt = TextHandler(nt.clean())
                if not case_sensitive: nt = TextHandler(nt.lower())
                if (partial and search_text in nt) or (not partial and search_text == nt): results.append(node)
                if first_match and results: break
        return results[0] if first_match and results else results
    @overload
    def find_by_regex(self, query, first_match: Literal[True] = ..., case_sensitive=..., clean_match=...) -> "Selector": ...
    @overload
    def find_by_regex(self, query, first_match: Literal[False], case_sensitive=..., clean_match=...) -> "Selectors": ...
    def find_by_regex(self, query, first_match=True, case_sensitive=False, clean_match=True) -> Union["Selectors", "Selector"]:
        if self._is_text_node(self._root): return Selectors()
        results = Selectors()
        possible = cast(List, _find_all_elements_with_spaces(self._root))
        if possible:
            for node in self.__elements_convertor(possible):
                if node.text.re(query, check_match=True, clean_match=clean_match, case_sensitive=case_sensitive): results.append(node)
                if first_match and results: break
        return results[0] if results and first_match else results

class Selectors(List[Selector]):
    __slots__ = ()
    @overload
    def __getitem__(self, pos: SupportsIndex) -> Selector: pass
    @overload
    def __getitem__(self, pos: slice) -> "Selectors": pass
    def __getitem__(self, pos: SupportsIndex | slice) -> Union[Selector, "Selectors"]:
        lst = super().__getitem__(pos)
        return self.__class__(cast(List[Selector], lst)) if isinstance(pos, slice) else cast(Selector, lst)
    def xpath(self, selector: str, identifier: str = "", auto_save=False, percentage=0, **kwargs) -> "Selectors":
        return self.__class__(flatten([n.xpath(selector, identifier or selector, False, auto_save, percentage, **kwargs) for n in self]))
    def css(self, selector: str, identifier: str = "", auto_save=False, percentage=0) -> "Selectors":
        return self.__class__(flatten([n.css(selector, identifier or selector, False, auto_save, percentage) for n in self]))
    def re(self, regex, replace_entities=True, clean_match=False, case_sensitive=True): return TextHandlers(flatten([n.re(regex, replace_entities, clean_match, case_sensitive) for n in self]))
    def re_first(self, regex, default=None, replace_entities=True, clean_match=False, case_sensitive=True):
        for n in self:
            for res in n.re(regex, replace_entities, clean_match, case_sensitive): return res
        return default
    def search(self, func: Callable[["Selector"], bool]) -> Optional["Selector"]:
        for element in self:
            if func(element): return element
        return None
    def filter(self, func: Callable[["Selector"], bool]) -> "Selectors": return self.__class__([e for e in self if func(e)])
    @overload
    def get(self) -> Optional[TextHandler]: ...
    @overload
    def get(self, default: _T) -> Union[TextHandler, _T]: ...
    def get(self, default=None):
        for x in self: return x.get()
        return default
    def getall(self) -> TextHandlers: return TextHandlers([x.get() for x in self])
    extract = getall
    extract_first = get
    @property
    def first(self) -> Optional[Selector]: return self[0] if len(self) > 0 else None
    @property
    def last(self) -> Optional[Selector]: return self[-1] if len(self) > 0 else None
    @property
    def length(self) -> int: return len(self)
    def __getstate__(self) -> Any: raise TypeError("Can't pickle Selectors object")

Adaptor = Selector
Adaptors = Selectors
