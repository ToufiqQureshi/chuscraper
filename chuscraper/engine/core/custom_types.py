from collections.abc import Mapping
from types import MappingProxyType
from re import compile as re_compile, UNICODE, IGNORECASE

from orjson import dumps, loads
from w3lib.html import replace_entities as _replace_entities

from chuscraper.engine.core._types import (
    Any,
    cast,
    Dict,
    List,
    Union,
    overload,
    TypeVar,
    Literal,
    Pattern,
    Iterable,
    Generator,
    SupportsIndex,
)
from chuscraper.engine.core.utils import _is_iterable, flatten, __CONSECUTIVE_SPACES_REGEX__

_TextHandlerType = TypeVar("_TextHandlerType", bound="TextHandler")
__CLEANING_TABLE__ = str.maketrans("\t\r\n", "   ")

class TextHandler(str):
    __slots__ = ()
    def __getitem__(self, key: SupportsIndex | slice) -> "TextHandler":
        lst = super().__getitem__(key)
        return TextHandler(lst)
    def split(self, sep: str | None = None, maxsplit: SupportsIndex = -1) -> list[Any]:
        return TextHandlers([TextHandler(s) for s in super().split(sep, maxsplit)])
    def strip(self, chars: str | None = None) -> Union[str, "TextHandler"]:
        return TextHandler(super().strip(chars))
    def lstrip(self, chars: str | None = None) -> Union[str, "TextHandler"]:
        return TextHandler(super().lstrip(chars))
    def rstrip(self, chars: str | None = None) -> Union[str, "TextHandler"]:
        return TextHandler(super().rstrip(chars))
    def capitalize(self) -> Union[str, "TextHandler"]:
        return TextHandler(super().capitalize())
    def casefold(self) -> Union[str, "TextHandler"]:
        return TextHandler(super().casefold())
    def center(self, width: SupportsIndex, fillchar: str = " ") -> Union[str, "TextHandler"]:
        return TextHandler(super().center(width, fillchar))
    def expandtabs(self, tabsize: SupportsIndex = 8) -> Union[str, "TextHandler"]:
        return TextHandler(super().expandtabs(tabsize))
    def format(self, *args: object, **kwargs: object) -> Union[str, "TextHandler"]:
        return TextHandler(super().format(*args, **kwargs))
    def format_map(self, mapping) -> Union[str, "TextHandler"]:
        return TextHandler(super().format_map(mapping))
    def join(self, iterable: Iterable[str]) -> Union[str, "TextHandler"]:
        return TextHandler(super().join(iterable))
    def ljust(self, width: SupportsIndex, fillchar: str = " ") -> Union[str, "TextHandler"]:
        return TextHandler(super().ljust(width, fillchar))
    def rjust(self, width: SupportsIndex, fillchar: str = " ") -> Union[str, "TextHandler"]:
        return TextHandler(super().rjust(width, fillchar))
    def swapcase(self) -> Union[str, "TextHandler"]:
        return TextHandler(super().swapcase())
    def title(self) -> Union[str, "TextHandler"]:
        return TextHandler(super().title())
    def translate(self, table) -> Union[str, "TextHandler"]:
        return TextHandler(super().translate(table))
    def zfill(self, width: SupportsIndex) -> Union[str, "TextHandler"]:
        return TextHandler(super().zfill(width))
    def replace(self, old: str, new: str, count: SupportsIndex = -1) -> Union[str, "TextHandler"]:
        return TextHandler(super().replace(old, new, count))
    def upper(self) -> Union[str, "TextHandler"]:
        return TextHandler(super().upper())
    def lower(self) -> Union[str, "TextHandler"]:
        return TextHandler(super().lower())
    def sort(self, reverse: bool = False) -> Union[str, "TextHandler"]:
        return self.__class__("".join(sorted(self, reverse=reverse)))
    def clean(self, remove_entities=False) -> Union[str, "TextHandler"]:
        data = self.translate(__CLEANING_TABLE__)
        if remove_entities:
            data = _replace_entities(data)
        return self.__class__(__CONSECUTIVE_SPACES_REGEX__.sub(" ", data).strip())
    def get(self, default=None): return self
    def get_all(self): return self
    extract = get_all
    extract_first = get
    def json(self) -> Dict: return loads(str(self))
    @overload
    def re(self, regex: str | Pattern, replace_entities: bool = True, clean_match: bool = False, case_sensitive: bool = True, *, check_match: Literal[True]) -> bool: ...
    @overload
    def re(self, regex: str | Pattern, replace_entities: bool = True, clean_match: bool = False, case_sensitive: bool = True, check_match: Literal[False] = False) -> "TextHandlers": ...
    def re(self, regex: str | Pattern, replace_entities: bool = True, clean_match: bool = False, case_sensitive: bool = True, check_match: bool = False) -> Union["TextHandlers", bool]:
        if isinstance(regex, str):
            flags = UNICODE if case_sensitive else UNICODE | IGNORECASE
            regex = re_compile(regex, flags)
        input_text = self.clean() if clean_match else self
        results = regex.findall(input_text)
        if check_match: return bool(results)
        if all(_is_iterable(res) for res in results): results = flatten(results)
        if not replace_entities: return TextHandlers([TextHandler(string) for string in results])
        return TextHandlers([TextHandler(_replace_entities(s)) for s in results])
    def re_first(self, regex: str | Pattern, default: Any = None, replace_entities: bool = True, clean_match: bool = False, case_sensitive: bool = True) -> "TextHandler":
        result = self.re(regex, replace_entities, clean_match=clean_match, case_sensitive=case_sensitive)
        return result[0] if result else default

class TextHandlers(List[TextHandler]):
    __slots__ = ()
    @overload
    def __getitem__(self, pos: SupportsIndex) -> TextHandler: pass
    @overload
    def __getitem__(self, pos: slice) -> "TextHandlers": pass
    def __getitem__(self, pos: SupportsIndex | slice) -> Union[TextHandler, "TextHandlers"]:
        lst = super().__getitem__(pos)
        if isinstance(pos, slice): return TextHandlers(cast(List[TextHandler], lst))
        return TextHandler(cast(TextHandler, lst))
    def re(self, regex: str | Pattern, replace_entities: bool = True, clean_match: bool = False, case_sensitive: bool = True) -> "TextHandlers":
        results = [n.re(regex, replace_entities, clean_match, case_sensitive) for n in self]
        return TextHandlers(flatten(results))
    def re_first(self, regex: str | Pattern, default: Any = None, replace_entities: bool = True, clean_match: bool = False, case_sensitive: bool = True) -> TextHandler:
        for n in self:
            for result in n.re(regex, replace_entities, clean_match, case_sensitive): return result
        return default
    def get(self, default=None): return self[0] if len(self) > 0 else default
    def extract(self): return self
    extract_first = get
    get_all = extract

class AttributesHandler(Mapping[str, _TextHandlerType]):
    __slots__ = ("_data",)
    def __init__(self, mapping: Any = None, **kwargs: Any) -> None:
        mapping = {key: TextHandler(value) if isinstance(value, str) else value for key, value in mapping.items()} if mapping is not None else {}
        if kwargs: mapping.update({key: TextHandler(value) if isinstance(value, str) else value for key, value in kwargs.items()})
        self._data: Mapping[str, Any] = MappingProxyType(mapping)
    def get(self, key: str, default: Any = None) -> _TextHandlerType: return self._data.get(key, default)
    def search_values(self, keyword: str, partial: bool = False) -> Generator["AttributesHandler", None, None]:
        for key, value in self._data.items():
            if partial:
                if keyword in value: yield AttributesHandler({key: value})
            else:
                if keyword == value: yield AttributesHandler({key: value})
    @property
    def json_string(self) -> bytes: return dumps(dict(self._data))
    def __getitem__(self, key: str) -> _TextHandlerType: return self._data[key]
    def __iter__(self): return iter(self._data)
    def __len__(self): return len(self._data)
    def __repr__(self): return f"{self.__class__.__name__}({self._data})"
    def __str__(self): return str(self._data)
    def __contains__(self, key): return key in self._data
