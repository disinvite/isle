import sqlite3
import logging
import json
from functools import cache
from typing import Any, Iterator, Optional

logger = logging.getLogger(__name__)

_SETUP_SQL = """
CREATE table uniball (
    uid integer primary key,
    source int unique,
    target int unique,
    symbol text unique,
    kwstore text not null default '{}'
);

CREATE view matched (uid, source, target, symbol, kwstore) as
select uid, source, target, symbol, kwstore from uniball where source is not null and target is not null order by source nulls last;

CREATE view unmatched (uid, source, target, symbol, kwstore) as
select uid, source, target, symbol, kwstore from uniball where source is null or target is null order by source nulls last;

CREATE index names ON uniball(JSON_EXTRACT(kwstore, '$.name'));
CREATE index types ON uniball(JSON_EXTRACT(kwstore, '$.type'));
"""


class MissingAnchorError(Exception):
    """Tried to create an Anchor reference without any unique id"""


@cache
def json_input(arg: frozenset) -> str:
    return json.dumps(dict(arg))


class Anchor:
    column: str
    value: Any

    def __init__(
        self,
        backref,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
    ) -> None:
        self._backref = backref

        if source is not None:
            self.column = "source"
            self.value = source
        elif target is not None:
            self.column = "target"
            self.value = target
        elif symbol is not None:
            self.column = "symbol"
            self.value = symbol
        else:
            raise MissingAnchorError

    def set(self, **kwargs):
        # TODO: hack?
        if self.column not in kwargs:
            kwargs[self.column] = self.value

        self._backref.set(self, **kwargs)


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
        anchor = Anchor(self._backref, self._source, self._target, self._symbol)
        self._backref.set(anchor, **kwargs)


class DudyCore:
    def __init__(self) -> None:
        self._sql = sqlite3.connect(":memory:")
        self._sql.executescript(_SETUP_SQL)
        # self._sql.set_trace_callback(print)

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

    def at_source(self, source: int) -> Anchor:
        return Anchor(self, source=source)

    def at_target(self, target: int) -> Anchor:
        return Anchor(self, target=target)

    def at_symbol(self, symbol: str) -> Anchor:
        return Anchor(self, symbol=symbol)

    def _opt_search(
        self, optkey: str, optval: Any, unmatched: bool = True
    ) -> Iterator[Nummy]:
        # TODO: add index here.
        # TODO: lol sql injection
        for source, target, symbol, extras in self._sql.execute(
            f"SELECT source, target, symbol, kwstore from uniball where json_extract(kwstore, '$.{optkey}') = ?",
            (optval,),
        ):
            if unmatched ^ (source is not None and target is not None):
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

    def search_type(self, type_: int, unmatched: bool = True) -> Iterator[Nummy]:
        return self._opt_search("type", type_, unmatched=unmatched)

    def search_name(self, name: str, unmatched: bool = True) -> Iterator[Nummy]:
        return self._opt_search("name", name, unmatched=unmatched)

    def search_symbol(self, query: str, unmatched: bool = True) -> Iterator[Nummy]:
        """Partial string search on symbol."""
        for source, target, symbol, extras in self._sql.execute(
            f"""SELECT source, target, symbol, kwstore FROM {'unmatched' if unmatched else 'uniball'} u
            where symbol like '%' || ? || '%'""",
            (query,),
        ):
            yield Nummy(self, source, target, symbol, extras)

    def all(self, matched: bool = False) -> Iterator[Nummy]:
        for source, target, symbol, extras in self._sql.execute(
            f"SELECT source, target, symbol, kwstore FROM {'matched' if matched else 'uniball'} order by source nulls last"
        ):
            yield Nummy(self, source, target, symbol, extras)

    def at(
        self,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
    ):
        """Generic `at` using optional args"""
        raise NotImplementedError

    def set(
        self,
        anchor: Anchor,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
        **kwargs,
    ):
        # pylint: disable=protected-access
        try:
            kwstore = json_input(frozenset(kwargs.items()))

            res = self._sql.execute(
                f"SELECT uid from uniball WHERE {anchor.column} = ?", (anchor.value,)
            ).fetchone()

            if res is None:
                self._sql.execute(
                    "INSERT into uniball (source, target, symbol, kwstore) values (?,?,?,?)",
                    (
                        source,
                        target,
                        symbol,
                        kwstore,
                    ),
                )
                return

            (uid,) = res
            self._sql.execute(
                """UPDATE uniball SET
                source = coalesce(source, ?),
                target = coalesce(target, ?),
                symbol = coalesce(symbol, ?),
                kwstore = json_patch(kwstore, ?)
                where uid = ?""",
                (source, target, symbol, kwstore, uid),
            )

        except sqlite3.Error as ex:
            raise ex  # todo
