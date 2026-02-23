from hashlib import sha256
from threading import RLock
from functools import lru_cache
from abc import ABC, abstractmethod
from sqlite3 import connect as db_connect

from orjson import dumps, loads
from lxml.html import HtmlElement

from chuscraper.engine.core.utils import _StorageTools, log
from chuscraper.engine.core._types import Dict, Optional, Any, cast

class StorageSystemMixin(ABC):
    def __init__(self, url: Optional[str] = None):
        self.url = url.lower() if (url and isinstance(url, str)) else None

    @lru_cache(64, typed=True)
    def _get_base_url(self, default_value: str = "default") -> str:
        if not self.url: return default_value
        try:
            from tld import get_tld, Result
            extracted: Result | None = cast(Result, get_tld(self.url, as_object=True, fail_silently=True, fix_protocol=True))
            if not extracted: return default_value
            return extracted.fld or extracted.domain or default_value
        except AttributeError: return default_value

    @abstractmethod
    def save(self, element: HtmlElement, identifier: str) -> None: pass
    @abstractmethod
    def retrieve(self, identifier: str) -> Optional[Dict]: pass

    @staticmethod
    @lru_cache(128, typed=True)
    def _get_hash(identifier: str) -> str:
        _identifier = identifier.lower().strip()
        _identifier_bytes = _identifier.encode("utf-8")
        hash_value = sha256(_identifier_bytes).hexdigest()
        return f"{hash_value}_{len(_identifier_bytes)}"

@lru_cache(1, typed=True)
class SQLiteStorageSystem(StorageSystemMixin):
    def __init__(self, storage_file: str, url: Optional[str] = None):
        super().__init__(url)
        self.storage_file = storage_file
        self.lock = RLock()
        self.connection = db_connect(self.storage_file, check_same_thread=False)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.cursor = self.connection.cursor()
        self._setup_database()
        log.debug(f'Storage system loaded')

    def _setup_database(self) -> None:
        self.cursor.execute("CREATE TABLE IF NOT EXISTS storage (id INTEGER PRIMARY KEY, url TEXT, identifier TEXT, element_data TEXT, UNIQUE (url, identifier))")
        self.connection.commit()

    def save(self, element: HtmlElement, identifier: str) -> None:
        url = self._get_base_url()
        element_data = _StorageTools.element_to_dict(element)
        with self.lock:
            self.cursor.execute("INSERT OR REPLACE INTO storage (url, identifier, element_data) VALUES (?, ?, ?)", (url, identifier, dumps(element_data)))
            self.cursor.fetchall()
            self.connection.commit()

    def retrieve(self, identifier: str) -> Optional[Dict[str, Any]]:
        url = self._get_base_url()
        with self.lock:
            self.cursor.execute("SELECT element_data FROM storage WHERE url = ? AND identifier = ?", (url, identifier))
            result = self.cursor.fetchone()
            if result: return loads(result[0])
            return None

    def close(self):
        with self.lock:
            try:
                self.connection.commit()
                self.cursor.close()
                self.connection.close()
            except: pass

    def __del__(self): self.close()
