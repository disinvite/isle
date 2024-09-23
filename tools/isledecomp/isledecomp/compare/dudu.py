import sqlite3
import logging
from collections import defaultdict
from typing import Any, Iterator, Optional

logger = logging.getLogger(__name__)

_SETUP_SQL = """
CREATE table uniball (
    uid integer not null primary key autoincrement,
    source int unique,
    target int unique,
    symbol text unique
);

CREATE view matched (uid, source, target, symbol) as
select uid, source, target, symbol from uniball where source is not null and target is not null order by source nulls last;

CREATE view unmatched (uid, source, target, symbol) as
select uid, source, target, symbol from uniball where source is null or target is null order by source nulls last;

CREATE table extras (
    uid int not null,
    optkey text not null collate nocase,
    optval,
    foreign key (uid) references uniball (uid),
    primary key (uid, optkey)
);

CREATE index options on extras (optkey, optval)
"""


class Nummy:
    # pylint: disable=R0801
    _uid: int
    _source: Optional[int] = None
    _target: Optional[int] = None
    _symbol: Optional[str] = None
    _extras: dict[str, Any]

    def __init__(
        self,
        backref,
        uid: int,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
    ) -> None:
        self._uid = uid
        self._source = source
        self._target = target
        self._symbol = symbol
        self._extras = defaultdict(lambda: None)

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
        return self._extras[key]

    def set(self, **kwargs):
        self._backref.set(self, **kwargs)


class DudyCore:
    def __init__(self) -> None:
        self._sql = sqlite3.connect(":memory:", isolation_level=None)
        self._sql.executescript(_SETUP_SQL)
        # self._sql.set_trace_callback(print)

        self._uids: dict[int, Nummy] = {}

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
                "SELECT uid from uniball where source = ?", (source,)
            ).fetchone()
        elif target is not None:
            res = self._sql.execute(
                "SELECT uid from uniball where target = ?", (target,)
            ).fetchone()
        elif symbol is not None:
            res = self._sql.execute(
                "SELECT uid from uniball where symbol = ?", (symbol,)
            ).fetchone()

        if res is None:
            return None

        return self._uids[res[0]]

    def at_source(self, source: int) -> Nummy:
        num = self.get(source=source)
        if num is None:
            (uid,) = self._sql.execute(
                "INSERT into uniball (source) values (?) returning uid", (source,)
            ).fetchone()
            num = Nummy(self, uid=uid, source=source)
            self._uids[uid] = num

        return num

    def at_target(self, target: int) -> Nummy:
        num = self.get(target=target)
        if num is None:
            (uid,) = self._sql.execute(
                "INSERT into uniball (target) values (?) returning uid", (target,)
            ).fetchone()
            num = Nummy(self, uid=uid, target=target)
            self._uids[uid] = num

        return num

    def at_symbol(self, symbol: str) -> Nummy:
        num = self.get(symbol=symbol)
        if num is None:
            (uid,) = self._sql.execute(
                "INSERT into uniball (symbol) values (?) returning uid", (symbol,)
            ).fetchone()
            num = Nummy(self, uid=uid, symbol=symbol)
            self._uids[uid] = num

        return num

    def _opt_search(
        self, optkey: str, optval: Any, unmatched: bool = True
    ) -> Iterator[Nummy]:
        for (uid,) in self._sql.execute(
            "SELECT uid from extras e where e.optkey = ? and e.optval = ?",
            (optkey, optval),
        ):
            nummy = self._uids[uid]
            if unmatched ^ (nummy.source is not None and nummy.target is not None):
                yield nummy

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
        for (uid,) in self._sql.execute(
            f"""SELECT uid FROM {'unmatched' if unmatched else 'uniball'} u
            where symbol like '%' || ? || '%'""",
            (query,),
        ):
            yield self._uids[uid]

    def all(self, matched: bool = False) -> Iterator[Nummy]:
        for (uid,) in self._sql.execute(
            f"SELECT uid FROM {'matched' if matched else 'uniball'} order by source nulls last"
        ):
            yield self._uids[uid]

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
        nummy: Nummy,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
        **kwargs,
    ):
        # pylint: disable=protected-access
        try:
            with self._sql:
                uid = nummy._uid
                if source or target or symbol:
                    new_source, new_target, new_symbol = self._sql.execute(
                        """UPDATE uniball set
                        source = coalesce(source, ?),
                        target = coalesce(target, ?),
                        symbol = coalesce(symbol, ?)
                        where uid = ?
                        returning source, target, symbol""",
                        (source, target, symbol, uid),
                    ).fetchone()

                    nummy._source = new_source
                    nummy._target = new_target
                    nummy._symbol = new_symbol

                values = [(uid, k, v) for k, v in kwargs.items()]
                self._sql.executemany(
                    "INSERT or replace into extras (uid, optkey, optval) values (?,?,?)",
                    values,
                )

                for k, v in kwargs.items():
                    if v is None and k in nummy._extras:
                        del nummy._extras[k]
                    else:
                        nummy._extras[k] = v

        except sqlite3.Error:
            pass # todo
