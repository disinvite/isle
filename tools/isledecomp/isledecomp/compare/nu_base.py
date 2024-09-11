import bisect
from collections import defaultdict
from typing import Any, Iterator, NewType, Optional
from isledecomp.types import SymbolType

UIDType = NewType("UIDType", int)


class MyIndex:
    def __init__(self) -> None:
        self._idx: dict[str, set[UIDType]] = defaultdict(set)
        self._rev: dict[UIDType, str] = {}

    def __getitem__(self, key: str) -> set[UIDType]:
        return self._idx[key]

    def set(self, uid: UIDType, key: Optional[str]):
        if (old_key := self._rev.get(uid)) is not None:
            if old_key == key:
                return

            self._idx[old_key].discard(uid)

        if key is not None:
            self._idx[key].add(uid)


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

    def __getitem__(self, addr: int) -> UIDType:
        return self._map[addr]

    def get(self, addr: int) -> Optional[UIDType]:
        return self._map.get(addr)

    def _sort(self):
        if not self._sorted:
            self._list = sorted(self._map.keys())
            self._sorted = True

    def __iter__(self) -> Iterator[tuple[int, UIDType]]:
        self._sort()
        for addr in self._list:
            yield (addr, self._map[addr])

    def prev(self, addr: int) -> Optional[int]:
        self._sort()
        i = bisect.bisect_left(self._list, addr)
        if i == 0:
            return None

        return self._list[i - 1]

    def next(self, addr: int) -> Optional[int]:
        self._sort()
        i = bisect.bisect_right(self._list, addr)
        if i == len(self._list):
            return None

        return self._list[i]


class DbObjectBase:
    _uid: UIDType
    _orig_addr: Optional[int] = None
    _recomp_addr: Optional[int] = None
    _name: Optional[str] = None
    _symbol: Optional[str] = None
    _ctype: Optional[SymbolType] = None
    size: Optional[int] = None

    def __init__(self, uid: UIDType, backref) -> None:
        self._uid = uid
        self._backref = backref

    @property
    def uid(self):
        return self._uid

    @property
    def orig_addr(self):
        return self._orig_addr

    @orig_addr.setter
    def orig_addr(self, value):
        self._backref.set_source(self._uid, value)
        self._orig_addr = value

    @property
    def recomp_addr(self):
        return self._recomp_addr

    @recomp_addr.setter
    def recomp_addr(self, value):
        self._backref.set_target(self._uid, value)
        self._recomp_addr = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._backref.set_name(self._uid, value)
        self._name = value

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self, value):
        self._symbol = value

    @property
    def type(self):
        return self._ctype

    @type.setter
    def type(self, value):
        self._ctype = value

    @property
    def compare_type(self):
        # TODO: double alias for compatibility with MatchInfo
        return self._ctype


class CompareCore:
    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-instance-attributes
    def __init__(self) -> None:
        self._cur_uid: int = 10000

        self._db: dict[UIDType, DbObjectBase] = {}
        self._src2uid = AddrMap()
        self._tgt2uid = AddrMap()
        self._name2uids = MyIndex()

        self._opt: dict[UIDType, dict[str, Any]] = defaultdict(dict)
        self._matched_uid: set[UIDType] = set()

    def _next_uid(self) -> DbObjectBase:
        uid = UIDType(self._cur_uid)
        self._cur_uid += 1

        self._db[uid] = DbObjectBase(uid, self)

        return self._db[uid]

    def get(self, uid: UIDType) -> DbObjectBase:
        return self._db[uid]

    def get_source(self, addr: int) -> Optional[UIDType]:
        return self._src2uid.get(addr)

    def get_target(self, addr: int) -> Optional[UIDType]:
        return self._tgt2uid.get(addr)

    def set_source(self, uid: UIDType, addr: int):
        if addr not in self._src2uid:
            self._src2uid[addr] = uid
            if self._db[uid].recomp_addr is not None:
                self._matched_uid.add(uid)

    def set_target(self, uid: UIDType, addr: int):
        if addr not in self._tgt2uid:
            self._tgt2uid[addr] = uid
            if self._db[uid].orig_addr is not None:
                self._matched_uid.add(uid)

    def set_name(self, uid: UIDType, name: Optional[str]):
        self._name2uids.set(uid, name)

    ####

    def get_symbol(self, symbol: str) -> Optional[UIDType]:
        # todo
        for uid, record in self._db.items():
            if record.symbol == symbol:
                return uid

        return None

    def get_name(self, name: str) -> Iterator[UIDType]:
        # Caution here: we use sets for the indices which do not guarantee order.
        # Revert to "insertion order" which should be the same as UID order.
        # Any order will do. It just needs to be consistent so matches of
        # non-unique names are stable.
        uids = list(self._name2uids[name])
        uids.sort()
        return iter(uids)

    def get_type(self, type_: SymbolType) -> Iterator[UIDType]:
        # todo
        for uid, record in self._db.items():
            if record.type == type_:
                yield uid

    ####

    def set_orig_symbol(
        self,
        addr: int,
        compare_type: Optional[SymbolType],
        name: Optional[str],
        size: Optional[int],
    ):
        if addr in self._src2uid:
            return

        obj = self._next_uid()
        obj.orig_addr = addr
        obj.name = name
        obj.size = size
        obj.type = compare_type

    def set_recomp_symbol(
        self,
        addr: int,
        compare_type: Optional[SymbolType],
        name: Optional[str],
        decorated_name: Optional[str],
        size: Optional[int],
    ):
        if addr in self._tgt2uid:
            return

        obj = self._next_uid()
        obj.recomp_addr = addr
        obj.name = name
        obj.symbol = decorated_name
        obj.size = size
        obj.type = compare_type

    ####

    def in_order(self, matched_only: bool = False) -> Iterator[UIDType]:
        """Iterator of uids ordered by source addr, nulls last."""
        for _, uid in self._src2uid:
            if not matched_only or uid in self._matched_uid:
                yield uid

        # Skip target-only unmatched
        if matched_only:
            return

        for _, uid in self._tgt2uid:
            if uid not in self._matched_uid:
                yield uid

    def describe(self, uid: UIDType, offset: int = 0) -> Optional[str]:
        """Return a string representation of this item. If an offset is given,
        add it to the item name. (This may be a struct member or array element.)
        Subclasses should override this to add custom behavior."""
        record = self._db[uid]
        if record.name is None:
            return None

        if offset > 0:
            return f"{record.name}+{offset}"

        return record.name
