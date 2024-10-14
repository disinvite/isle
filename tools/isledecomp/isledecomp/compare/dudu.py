import sqlite3
import logging
import json
from typing import Any, Iterator, Optional

logger = logging.getLogger(__name__)

_SETUP_SQL = """
CREATE table reversi (
    uid integer primary key,
    source int unique,
    target int unique,
    symbol text unique,
    matched int generated always as (source is not null and target is not null) virtual,
    kwstore text
);
"""


class InvalidItemKeyError(Exception):
    """Key used in search() or set() failed validation"""


class MissingAnchorError(Exception):
    """Tried to create an Anchor reference without any unique id"""


class AnchorSource:
    # pylint: disable=unused-argument
    def __init__(self, sql: sqlite3.Connection, source: int) -> None:
        self._sql = sql
        self._source = source

    def _exists(self) -> bool:
        return (
            self._sql.execute(
                "SELECT 1 from reversi WHERE source = ?", (self._source,)
            ).fetchone()
            is not None
        )

    def _insert(
        self,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
        **kwargs,
    ):
        self._sql.execute(
            "INSERT into reversi (source, target, symbol, kwstore) values (?,?,?,?)",
            (self._source, target, symbol, json.dumps(kwargs)),
        )

    def _update(
        self,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
        **kwargs,
    ):
        self._sql.execute(
            "UPDATE reversi SET target = coalesce(target, ?), symbol = coalesce(symbol, ?), kwstore = json_patch(kwstore,?) where source = ?",
            (target, symbol, json.dumps(kwargs), self._source),
        )

    def insert(
        self,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
        **kwargs,
    ):
        self._sql.execute(
            "INSERT into reversi (source, target, symbol, kwstore) values (?,?,?,?) ON CONFLICT(source) do nothing",
            (self._source, target, symbol, json.dumps(kwargs)),
        )

    def set(self, **kwargs):
        if not self._exists():
            self._insert(**kwargs)
            return

        self._update(**kwargs)


class AnchorTarget:
    # pylint: disable=unused-argument
    def __init__(self, sql: sqlite3.Connection, target: int) -> None:
        self._sql = sql
        self._target = target

    def _exists(self) -> bool:
        return (
            self._sql.execute(
                "SELECT 1 from reversi WHERE target = ?", (self._target,)
            ).fetchone()
            is not None
        )

    def _insert(
        self,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
        **kwargs,
    ):
        self._sql.execute(
            "INSERT into reversi (source, target, symbol, kwstore) values (?,?,?,?)",
            (source, self._target, symbol, json.dumps(kwargs)),
        )

    def _update(
        self,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
        **kwargs,
    ):
        self._sql.execute(
            "UPDATE reversi SET source = coalesce(source, ?), symbol = coalesce(symbol, ?), kwstore = json_patch(kwstore,?) where target = ?",
            (source, symbol, json.dumps(kwargs), self._target),
        )

    def insert(
        self,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
        **kwargs,
    ):
        self._sql.execute(
            "INSERT into reversi (source, target, symbol, kwstore) values (?,?,?,?) ON CONFLICT(target) do nothing",
            (source, self._target, symbol, json.dumps(kwargs)),
        )

    def set(self, **kwargs):
        if not self._exists():
            self._insert(**kwargs)
            return

        self._update(**kwargs)


class AnchorSymbol:
    # pylint: disable=unused-argument
    def __init__(self, sql: sqlite3.Connection, symbol: str) -> None:
        self._sql = sql
        self._symbol = symbol

    def _exists(self) -> bool:
        return (
            self._sql.execute(
                "SELECT 1 from reversi WHERE symbol = ?", (self._symbol,)
            ).fetchone()
            is not None
        )

    def _insert(
        self,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
        **kwargs,
    ):
        self._sql.execute(
            "INSERT into reversi (source, target, symbol, kwstore) values (?,?,?,?)",
            (source, target, self._symbol, json.dumps(kwargs)),
        )

    def _update(
        self,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
        **kwargs,
    ):
        self._sql.execute(
            "UPDATE reversi SET source = coalesce(source, ?), target = coalesce(target, ?), kwstore = json_patch(kwstore,?) where symbol = ?",
            (source, target, json.dumps(kwargs), self._symbol),
        )

    def insert(
        self,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
        **kwargs,
    ):
        self._sql.execute(
            "INSERT into reversi (source, target, symbol, kwstore) values (?,?,?,?) ON CONFLICT(symbol) do nothing",
            (source, target, self._symbol, json.dumps(kwargs)),
        )

    def set(self, **kwargs):
        if not self._exists():
            self._insert(**kwargs)
            return

        self._update(**kwargs)


class ReversiThing:
    # pylint: disable=R0801
    _source: Optional[int]
    _target: Optional[int]
    _symbol: Optional[str]
    _extras: dict[str, Any]

    def __init__(
        self,
        backref,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
        extras: Optional[str] = None,
    ) -> None:
        self._source = source
        self._target = target
        self._symbol = symbol
        self._extras = {}

        if extras is not None:
            self._extras = json.loads(extras)

        self._backref = backref

    def __repr__(self) -> str:
        (src, tgt, sym) = (self._source, self._target, self._symbol)
        return ", ".join(
            [
                f"ReversiThing(name={self.get('name') or 'None'}",
                f"src={hex(src) if src is not None else 'None'}",
                f"tgt={hex(tgt) if tgt is not None else 'None'}",
                f"sym={sym or 'None'})",
            ]
        )

    @property
    def source(self) -> Optional[int]:
        return self._source

    @property
    def target(self) -> Optional[int]:
        return self._target

    @property
    def symbol(self) -> Optional[str]:
        return self._symbol

    @property
    def matched(self) -> bool:
        return self._source is not None and self._target is not None

    def get(self, key: str) -> Any:
        return self._extras.get(key)

    def set(self, **kwargs):
        # pylint: disable=protected-access
        # TODO: woof
        if self._source is not None:
            AnchorSource(self._backref._sql, self._source).set(**kwargs)
        elif self._target is not None:
            AnchorTarget(self._backref._sql, self._target).set(**kwargs)
        elif self._symbol is not None:
            AnchorSymbol(self._backref._sql, self._symbol).set(**kwargs)
        else:
            raise NotImplementedError


class ReversiDb:
    SPECIAL_COLS = frozenset({"rowid", "uid", "source", "target", "matched", "kwstore"})

    def __init__(self) -> None:
        self._sql = sqlite3.connect(":memory:")
        self._sql.executescript(_SETUP_SQL)
        # self._sql.set_trace_callback(print)

        self._indexed: set[str] = set()

    @classmethod
    def check_kwargs(cls, kwargs):
        for key, _ in kwargs.items():
            if not key.isascii() or not key.isidentifier():
                raise InvalidItemKeyError(key)

    def orig_used(self, addr: int) -> bool:
        return (
            self._sql.execute(
                "SELECT 1 from reversi where source = ?", (addr,)
            ).fetchone()
            is not None
        )

    def recomp_used(self, addr: int) -> bool:
        return (
            self._sql.execute(
                "SELECT 1 from reversi where target = ?", (addr,)
            ).fetchone()
            is not None
        )

    def get_source(self, source: int) -> Optional[ReversiThing]:
        res = self._sql.execute(
            "SELECT source, target, symbol, kwstore from reversi where source = ?",
            (source,),
        ).fetchone()
        if res is None:
            return None

        return ReversiThing(self, *res)

    def get_target(self, target: int) -> Optional[ReversiThing]:
        res = self._sql.execute(
            "SELECT source, target, symbol, kwstore from reversi where target = ?",
            (target,),
        ).fetchone()
        if res is None:
            return None

        return ReversiThing(self, *res)

    def get_symbol(self, symbol: str) -> Optional[ReversiThing]:
        res = self._sql.execute(
            "SELECT source, target, symbol, kwstore from reversi where symbol = ?",
            (symbol,),
        ).fetchone()
        if res is None:
            return None

        return ReversiThing(self, *res)

    def get_closest_source(self, source: int) -> Optional[ReversiThing]:
        for res in self._sql.execute(
            "SELECT source, target, symbol, kwstore from reversi where source <= ? order by source desc limit 1",
            (source,),
        ):
            return ReversiThing(self, *res)

        return None

    def get_closest_target(self, target: int) -> Optional[ReversiThing]:
        for res in self._sql.execute(
            "SELECT source, target, symbol, kwstore from reversi where target <= ? order by target desc limit 1",
            (target,),
        ):
            return ReversiThing(self, *res)

        return None

    def at_source(self, source: int) -> AnchorSource:
        return AnchorSource(self._sql, source)

    def at_target(self, target: int) -> AnchorTarget:
        return AnchorTarget(self._sql, target)

    def at_symbol(self, symbol: str) -> AnchorSymbol:
        return AnchorSymbol(self._sql, symbol)

    def search(
        self, matched: Optional[bool] = None, **kwargs
    ) -> Iterator[ReversiThing]:
        """Search the database for each of the key-value pairs in kwargs.
        The virtual column 'matched' is handled separately from kwargs because we do
        not use the json functions.

        TODO:
        If the given key argument is None, check the value for NULL.
        If the given key argument is a sequence, use an IN condition to check multiple values.
        """

        # To create and use an index on the json_extract() expression, we cannot
        # parameterize the key name in the query text. This of course leaves us vulnerable
        # to a SQL injection attack. However: we restrict the allowed kwarg keys to
        # ASCII strings that are valid python identifiers, so this should eliminate the risk.
        self.check_kwargs(kwargs)

        # Foreach kwarg without an index, create one
        for optkey in kwargs.keys() - self.SPECIAL_COLS - self._indexed:
            self._sql.execute(
                f"CREATE index kv_idx_{optkey} ON reversi(JSON_EXTRACT(kwstore, '$.{optkey}'))"
            )
            self._indexed.add(optkey)

        search_terms = [
            f"json_extract(kwstore, '$.{optkey}')=?" for optkey, _ in kwargs.items()
        ]
        if matched is not None:
            search_terms.append(f"matched = {'true' if matched else 'false'}")

        q_params = [v for _, v in kwargs.items()]

        # Hide WHERE clause if mached is None and there are no kwargs
        where_clause = (
            "" if len(search_terms) == 0 else (" where " + " and ".join(search_terms))
        )

        for source, target, symbol, extras in self._sql.execute(
            "SELECT source, target, symbol, kwstore from reversi" + where_clause,
            q_params,
        ):
            yield ReversiThing(self, source, target, symbol, extras)

    def iter_source(self, source: int, reverse: bool = False) -> Iterator[int]:
        if reverse:
            sql = "SELECT source from reversi where source <= ? order by source desc"
        else:
            sql = "SELECT source from reversi where source >= ? order by source"

        for (addr,) in self._sql.execute(sql, (source,)):
            yield addr

    def iter_target(self, target: int, reverse: bool = False) -> Iterator[int]:
        if reverse:
            sql = "SELECT target from reversi where target <= ? order by target desc"
        else:
            sql = "SELECT target from reversi where target >= ? order by target"

        for (addr,) in self._sql.execute(sql, (target,)):
            yield addr

    def search_symbol(self, query: str) -> Iterator[str]:
        """Partial string search on symbol."""
        for (symbol,) in self._sql.execute(
            "SELECT symbol FROM reversi where symbol like '%' || ? || '%'", (query,)
        ):
            yield symbol

    def all(self, matched: Optional[bool] = None) -> Iterator[ReversiThing]:
        # TODO: apart from the 'order by', this is identical to a search with no kwargs.
        # consolidate the two functions?
        query = " ".join(
            [
                "SELECT source, target, symbol, kwstore FROM reversi",
                (
                    ""
                    if matched is None
                    else f"where matched = {'true' if matched else 'false'}"
                ),
                "order by source nulls last",
            ]
        )
        for source, target, symbol, extras in self._sql.execute(query):
            yield ReversiThing(self, source, target, symbol, extras)
