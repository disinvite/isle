import sqlite3
import logging
import json
from typing import Any, Iterator, Optional

logger = logging.getLogger(__name__)

_SETUP_SQL = """
CREATE table uniball (
    uid integer primary key,
    source int unique,
    target int unique,
    symbol text unique,
    matched int generated always as (source is not null and target is not null) virtual,
    kwstore text
);

CREATE view matched (uid, source, target, symbol, kwstore) as
select uid, source, target, symbol, kwstore from uniball where source is not null and target is not null order by source nulls last;

CREATE view unmatched (uid, source, target, symbol, kwstore) as
select uid, source, target, symbol, kwstore from uniball where source is null or target is null order by source nulls last;
"""


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
                "SELECT 1 from uniball WHERE source = ?", (self._source,)
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
            "INSERT into uniball (source, target, symbol, kwstore) values (?,?,?,?)",
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
            "UPDATE uniball SET target = coalesce(target, ?), symbol = coalesce(symbol, ?), kwstore = json_patch(kwstore,?) where source = ?",
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
            "INSERT into uniball (source, target, symbol, kwstore) values (?,?,?,?) ON CONFLICT(source) do nothing",
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
                "SELECT 1 from uniball WHERE target = ?", (self._target,)
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
            "INSERT into uniball (source, target, symbol, kwstore) values (?,?,?,?)",
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
            "UPDATE uniball SET source = coalesce(source, ?), symbol = coalesce(symbol, ?), kwstore = json_patch(kwstore,?) where target = ?",
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
            "INSERT into uniball (source, target, symbol, kwstore) values (?,?,?,?) ON CONFLICT(target) do nothing",
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
                "SELECT 1 from uniball WHERE symbol = ?", (self._symbol,)
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
            "INSERT into uniball (source, target, symbol, kwstore) values (?,?,?,?)",
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
            "UPDATE uniball SET source = coalesce(source, ?), target = coalesce(target, ?), kwstore = json_patch(kwstore,?) where symbol = ?",
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
            "INSERT into uniball (source, target, symbol, kwstore) values (?,?,?,?) ON CONFLICT(symbol) do nothing",
            (source, target, self._symbol, json.dumps(kwargs)),
        )

    def set(self, **kwargs):
        if not self._exists():
            self._insert(**kwargs)
            return

        self._update(**kwargs)


class Nummy:
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
                f"Nummy(name={self.get('name') or 'None'}",
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


class DudyCore:
    SPECIAL_COLS = frozenset({"rowid", "uid", "source", "target", "matched", "kwstore"})

    def __init__(self) -> None:
        self._sql = sqlite3.connect(":memory:")
        self._sql.executescript(_SETUP_SQL)
        # self._sql.set_trace_callback(print)

        self._indexed: set[str] = set()

    def orig_used(self, addr: int) -> bool:
        return (
            self._sql.execute(
                "SELECT 1 from uniball where source = ?", (addr,)
            ).fetchone()
            is not None
        )

    def recomp_used(self, addr: int) -> bool:
        return (
            self._sql.execute(
                "SELECT 1 from uniball where target = ?", (addr,)
            ).fetchone()
            is not None
        )

    def get(
        self,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
    ) -> Optional[Nummy]:
        """This only returns an object; it does not create one"""
        res = None

        if source is not None:
            res = self._sql.execute(
                "SELECT source, target, symbol, kwstore from uniball where source = ?",
                (source,),
            ).fetchone()
        elif target is not None:
            res = self._sql.execute(
                "SELECT source, target, symbol, kwstore from uniball where target = ?",
                (target,),
            ).fetchone()
        elif symbol is not None:
            res = self._sql.execute(
                "SELECT source, target, symbol, kwstore from uniball where symbol = ?",
                (symbol,),
            ).fetchone()

        if res is None:
            return None

        # TODO: hack
        return Nummy(self, *res)

    def _get_uid(
        self,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
    ) -> Optional[int]:
        """TODO: hack but this keeps the uid internal and establishes our priority for unique ids"""
        res = None

        if source is not None:
            res = self._sql.execute(
                "SELECT uid from uniball where source = ?", (source,)
            ).fetchone()

        if res is None and target is not None:
            res = self._sql.execute(
                "SELECT uid from uniball where target = ?", (target,)
            ).fetchone()

        if res is None and symbol is not None:
            res = self._sql.execute(
                "SELECT uid from uniball where symbol = ?", (symbol,)
            ).fetchone()

        if res is None:
            return None

        return res[0]

    def get_covering(
        self, source: Optional[int] = None, target: Optional[int] = None
    ) -> Optional[Nummy]:
        """For the given source or target addr, find the record that most likely `contains` the address.
        Meaning: if the address is a jump label in a function, get the parent function.
        If it is an offset of a struct/array, get the main address."""
        # TODO: For the moment we are just getting the previous address.
        res = None

        if source is not None:
            res = self._sql.execute(
                "SELECT source, target, symbol, kwstore from uniball where source <= ? order by source desc limit 1",
                (source,),
            ).fetchone()
        elif target is not None:
            res = self._sql.execute(
                "SELECT source, target, symbol, kwstore from uniball where target <= ? order by target desc limit 1",
                (target,),
            ).fetchone()

        if res is None:
            return None

        # TODO: hack
        return Nummy(self, *res)

    def at_source(self, source: int) -> AnchorSource:
        return AnchorSource(self._sql, source)

    def at_target(self, target: int) -> AnchorTarget:
        return AnchorTarget(self._sql, target)

    def at_symbol(self, symbol: str) -> AnchorSymbol:
        return AnchorSymbol(self._sql, symbol)

    def _opt_search(self, matched: Optional[bool] = None, **kwargs) -> Iterator[Nummy]:
        # TODO
        assert len(kwargs) > 0

        # TODO: lol sql injection
        for optkey, _ in kwargs.items():
            if optkey not in self.SPECIAL_COLS and optkey not in self._indexed:
                self._sql.execute(
                    f"CREATE index kv_idx_{optkey} ON uniball(JSON_EXTRACT(kwstore, '$.{optkey}'))"
                )
                self._indexed.add(optkey)

        search_terms = [
            f"json_extract(kwstore, '$.{optkey}')=?" for optkey, _ in kwargs.items()
        ]
        if matched is not None:
            search_terms.append(f"matched = {'true' if matched else 'false'}")

        q_params = [v for _, v in kwargs.items()]

        for source, target, symbol, extras in self._sql.execute(
            "SELECT source, target, symbol, kwstore from uniball where "
            + " and ".join(search_terms),
            q_params,
        ):
            yield Nummy(self, source, target, symbol, extras)

    def iter_source(self, source: int, reverse: bool = False) -> Iterator[int]:
        if reverse:
            sql = "SELECT source from uniball where source <= ? order by source desc"
        else:
            sql = "SELECT source from uniball where source >= ? order by source"

        for (addr,) in self._sql.execute(sql, (source,)):
            yield addr

    def iter_target(self, target: int, reverse: bool = False) -> Iterator[int]:
        if reverse:
            sql = "SELECT target from uniball where target <= ? order by target desc"
        else:
            sql = "SELECT target from uniball where target >= ? order by target"

        for (addr,) in self._sql.execute(sql, (target,)):
            yield addr

    def search_type(
        self, type_: int, matched: Optional[bool] = None
    ) -> Iterator[Nummy]:
        return self._opt_search(type=type_, matched=matched)

    def search_name(self, name: str, matched: Optional[bool] = None) -> Iterator[Nummy]:
        return self._opt_search(name=name, matched=matched)

    def search_symbol(self, query: str, unmatched: bool = True) -> Iterator[Nummy]:
        """Partial string search on symbol."""
        for source, target, symbol, extras in self._sql.execute(
            f"""SELECT source, target, symbol, kwstore FROM {'unmatched' if unmatched else 'uniball'} u
            where symbol like '%' || ? || '%'""",
            (query,),
        ):
            yield Nummy(self, source, target, symbol, extras)

    def all(self, matched: Optional[bool] = None) -> Iterator[Nummy]:
        query = " ".join(
            [
                "SELECT source, target, symbol, kwstore FROM uniball",
                (
                    ""
                    if matched is None
                    else f"where matched = {'true' if matched else 'false'}"
                ),
                "order by source nulls last",
            ]
        )
        for source, target, symbol, extras in self._sql.execute(query):
            yield Nummy(self, source, target, symbol, extras)

    def at(
        self,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
    ):
        """Generic `at` using optional args"""
        raise NotImplementedError
