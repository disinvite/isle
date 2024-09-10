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


class JITSortedList:
    """Just In Time sorted list. Throw items on the pile until we invoke one
    of the iterators. From then on, protect the order with bisect.insort"""

    def __init__(self) -> None:
        self._list: list[int] = []
        self._sorted: bool = False

    def _sort(self):
        if not self._sorted:
            self._list.sort()
            self._sorted = True

    def __iter__(self) -> Iterator[int]:
        self._sort()
        return iter(self._list)

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

    def add(self, addr: int):
        if self._sorted:
            bisect.insort(self._list, addr)
        else:
            self._list.append(addr)


class CompareCore:
    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-instance-attributes
    def __init__(self) -> None:
        self._cur_uid: int = 10000

        self._db: dict[UIDType, dict[str, Any]] = {}
        self._src2uid: dict[int, UIDType] = {}
        self._tgt2uid: dict[int, UIDType] = {}
        self._name2uids = MyIndex()

        self._opt: dict[UIDType, dict[str, Any]] = defaultdict(dict)
        self._matched_uid: set[UIDType] = set()

        self._src_order = JITSortedList()
        self._tgt_order = JITSortedList()

    def _next_uid(self) -> UIDType:
        uid = UIDType(self._cur_uid)
        self._cur_uid += 1
        # todo: Establish obj here?
        self._db[uid] = {
            "orig_addr": None,
            "recomp_addr": None,
            "type": None,
            "name": None,
            "symbol": None,
            "size": None,
        }

        return uid

    def get(self, uid: UIDType) -> dict[str, Any]:
        return self._db[uid]

    def get_source(self, addr: int) -> Optional[UIDType]:
        return self._src2uid.get(addr)

    def get_target(self, addr: int) -> Optional[UIDType]:
        return self._tgt2uid.get(addr)

    def set_source(self, uid: UIDType, addr: int):
        if addr not in self._src2uid:
            self._src2uid[addr] = uid
            self._src_order.add(addr)
            self._db[uid]["orig_addr"] = addr
            if self._db[uid]["recomp_addr"] is not None:
                self._matched_uid.add(uid)

    def set_target(self, uid: UIDType, addr: int):
        if addr not in self._tgt2uid:
            self._tgt2uid[addr] = uid
            self._tgt_order.add(addr)
            self._db[uid]["recomp_addr"] = addr
            if self._db[uid]["orig_addr"] is not None:
                self._matched_uid.add(uid)

    def set_size(self, uid: UIDType, size: Optional[int]):
        # todo: maybe more here.
        self._db[uid]["size"] = size

    def set_symbol(self, uid: UIDType, symbol: Optional[str]):
        # todo: index
        self._db[uid]["symbol"] = symbol

    def set_name(self, uid: UIDType, name: Optional[str]):
        self._name2uids.set(uid, name)
        self._db[uid]["name"] = name

    def set_type(self, uid: UIDType, type_: Optional[SymbolType]):
        # todo: index
        self._db[uid]["type"] = type_

    def set_option(self, uid: UIDType, key: str, value: Any):
        # todo
        raise NotImplementedError

    ####

    def get_symbol(self, symbol: str) -> Optional[UIDType]:
        # todo
        for uid, record in self._db.items():
            if record["symbol"] == symbol:
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
            if record["type"] == type_:
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

        uid = self._next_uid()
        self.set_source(uid, addr)
        self.set_name(uid, name)
        self.set_size(uid, size)
        self.set_type(uid, compare_type)

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

        uid = self._next_uid()
        self.set_target(uid, addr)
        self.set_name(uid, name)
        self.set_symbol(uid, decorated_name)
        self.set_size(uid, size)
        self.set_type(uid, compare_type)

    ####

    def in_order(self, matched_only: bool = False) -> Iterator[UIDType]:
        """Iterator of uids ordered by source addr, nulls last."""
        for addr in self._src_order:
            uid = self._src2uid[addr]
            if not matched_only or uid in self._matched_uid:
                yield uid

        # Skip target-only unmatched
        if matched_only:
            return

        for addr in self._tgt_order:
            uid = self._tgt2uid[addr]
            if uid not in self._matched_uid:
                yield uid
