import bisect
import logging
from collections import defaultdict
from typing import Any, Iterator, NewType, Optional

logger = logging.getLogger(__name__)

UIDType = NewType("UIDType", int)


class AddrMap:
    """Virtual address to UID. Combination dict and ordered list (by addr).
    Address order is maintained by bisect.insort, but we defer this until we
    need to iterate over the list."""

    def __init__(self) -> None:
        self._map: dict[int, UIDType] = {}
        self._list: list[int] = []
        self._sorted = False

    def __contains__(self, addr: int) -> bool:
        return addr in self._map

    def __setitem__(self, addr: int, uid: UIDType):
        if addr in self._map:
            return

        self._map[addr] = uid
        if self._sorted:
            bisect.insort(self._list, addr)

    def __delitem__(self, value: Optional[int]):
        if value is None:
            return

        del self._map[value]
        if self._sorted:
            self._list.remove(value)

    def __getitem__(self, addr: int) -> UIDType:
        return self._map[addr]

    def get(self, addr: int) -> Optional[UIDType]:
        return self._map.get(addr)

    def __iter__(self) -> Iterator[tuple[int, UIDType]]:
        if not self._sorted:
            self._list = sorted(self._map.keys())
            self._sorted = True

        for addr in self._list:
            yield (addr, self._map[addr])

    def prev(self, addr: int) -> Optional[int]:
        if not self._sorted:
            self._list = sorted(self._map.keys())
            self._sorted = True

        i = bisect.bisect_left(self._list, addr)
        if i == 0:
            return None

        return self._list[i - 1]

    def next(self, addr: int) -> Optional[int]:
        if not self._sorted:
            self._list = sorted(self._map.keys())
            self._sorted = True

        i = bisect.bisect_right(self._list, addr)
        if i == len(self._list):
            return None

        return self._list[i]

    def prev_or_cur(self, addr: int) -> Optional[UIDType]:
        if addr in self._map:
            return self._map[addr]

        prev = self.prev(addr)
        if prev is not None:
            return self._map[prev]

        return None


class Nummy:
    # pylint: disable=R0801
    _uid: UIDType
    _source: Optional[int] = None
    _target: Optional[int] = None
    _symbol: Optional[str] = None
    _extras: dict[str, Any]

    def __init__(
        self,
        backref,
        uid: UIDType,
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
        self._next_uid: int = 10000
        self._uids: dict[UIDType, Nummy] = {}
        # cross-ref for tuples in uids
        self._sources = AddrMap()
        self._targets = AddrMap()
        self._symbols: dict[str, UIDType] = {}

        # cross-ref for options. [key][value] -> set of uids.
        self._index = defaultdict(lambda: defaultdict(set))

    def _get_uid(self) -> UIDType:
        uid = UIDType(self._next_uid)
        self._next_uid += 1
        return uid

    def orig_used(self, addr: int) -> bool:
        return addr in self._sources

    def recomp_used(self, addr: int) -> bool:
        return addr in self._targets

    def get(
        self,
        source: Optional[int] = None,
        target: Optional[int] = None,
        symbol: Optional[str] = None,
    ) -> Optional[Nummy]:
        """This only returns an object; it does not create one"""
        uid: Optional[UIDType] = None
        if source is not None:
            uid = self._sources.get(source)
        elif target is not None:
            uid = self._targets.get(target)
        elif symbol is not None:
            uid = self._symbols.get(symbol)

        if uid is not None:
            return self._uids[uid]

        return None

    def get_covering(
        self, source: Optional[int] = None, target: Optional[int] = None
    ) -> Optional[Nummy]:
        """For the given source or target addr, find the record that most likely `contains` the address.
        Meaning: if the address is a jump label in a function, get the parent function.
        If it is an offset of a struct/array, get the main address."""
        # TODO: For the moment we are just getting the previous address.
        uid = None

        if source is not None:
            uid = self._sources.prev_or_cur(source)
        elif target is not None:
            uid = self._targets.prev_or_cur(target)

        if uid is None:
            return None

        return self._uids[uid]

    def at_source(self, source: int) -> Nummy:
        uid = self._sources.get(source)
        if uid is None:
            uid = self._get_uid()
            self._sources[source] = uid
            self._uids[uid] = Nummy(self, uid=uid, source=source)

        return self._uids[uid]

    def at_target(self, target: int) -> Nummy:
        uid = self._targets.get(target)
        if uid is None:
            uid = self._get_uid()
            self._targets[target] = uid
            self._uids[uid] = Nummy(self, uid=uid, target=target)

        return self._uids[uid]

    def at_symbol(self, symbol: str) -> Nummy:
        uid = self._symbols.get(symbol)
        if uid is None:
            uid = self._get_uid()
            self._symbols[symbol] = uid
            self._uids[uid] = Nummy(self, uid=uid, symbol=symbol)

        return self._uids[uid]

    def get_options(self, uid: UIDType) -> dict[str, Any]:
        """Todo"""
        return self._uids[uid]._extras or {}  # pylint: disable=protected-access
        # return self._options.get(uid, {})

    def _opt_search(
        self, optkey: str, optval: Any, unmatched: bool = True
    ) -> Iterator[Nummy]:
        # NB: We have to sort by UID here. Python sets do not guarantee order.
        # Sorting by numeric uid will equal "insertion order".
        # This is required so that matches on identical name/value will be stable between runs.
        for uid in sorted(self._index[optkey][optval]):
            nummy = self._uids[uid]
            if unmatched ^ (nummy.source is not None and nummy.target is not None):
                yield nummy

    def iter_source(self, source: int, reverse: bool = False) -> Iterator[int]:
        # todo: hack
        if source in self._sources:
            yield source

        if reverse:
            yield self._sources.prev(source)
        else:
            yield self._sources.next(source)

    def iter_target(self, target: int, reverse: bool = False) -> Iterator[int]:
        # todo: hack
        if target in self._targets:
            yield target

        if reverse:
            yield self._targets.prev(target)
        else:
            yield self._targets.next(target)

    def search_type(self, type_: int, unmatched: bool = True) -> Iterator[Nummy]:
        return self._opt_search("type", type_, unmatched=unmatched)

    def search_name(self, name: str, unmatched: bool = True) -> Iterator[Nummy]:
        return self._opt_search("name", name, unmatched=unmatched)

    def search_symbol(self, query: str, unmatched: bool = True) -> Iterator[Nummy]:
        """Partial string search on symbol."""
        for sym, uid in self._symbols.items():
            if query in sym:
                num = self._uids[uid]
                if not unmatched or (num.source is None or num.target is None):
                    yield num

    def all(self, matched: bool = False) -> Iterator[Nummy]:
        """Ordered by source addr (matched/unmatched) then target addr unmatched"""
        for _, uid in self._sources:
            num = self._uids[uid]
            if not matched or num.source is not None and num.target is not None:
                yield num

        # If we only want matched, end here. These are the leftover recomp items.
        if not matched:
            for _, uid in self._targets:
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
        """source/target/symbol pulled out of kwargs here.
        todo: Do we need lower case conversion here?"""

        uid = nummy._uid

        if source is not None and nummy.source != source:
            assert source not in self._sources
            nummy._source = source
            self._sources[source] = uid

        if target is not None and nummy.target != target:
            assert target not in self._targets
            nummy._target = target
            self._targets[target] = uid

        if symbol is not None and nummy.symbol != symbol:
            assert symbol not in self._symbols
            nummy._symbol = symbol
            self._symbols[symbol] = uid

        # TODO: check for empty options dict?
        if len(nummy._extras) == 0:
            for k, v in kwargs.items():
                if v is not None:
                    nummy._extras[k] = v
                    self._index[k][v].add(uid)

            return

        for k, v in kwargs.items():
            if k not in nummy._extras:
                # Don't bother replacing null with null.
                if v is None:
                    continue

                nummy._extras[k] = v
                self._index[k][v].add(uid)
            else:
                oldval = nummy._extras[k]
                if v == oldval:
                    continue

                self._index[k][oldval].discard(uid)

                if v is None:
                    del nummy._extras[k]
                else:
                    nummy._extras[k] = v
                    self._index[k][v].add(uid)
