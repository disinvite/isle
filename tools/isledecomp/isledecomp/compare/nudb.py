import bisect
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterator, NewType, Optional
from isledecomp.types import SymbolType
from isledecomp.cvdump.demangler import get_vtordisp_name

UIDType = NewType("UIDType", int)
logger = logging.getLogger(__name__)


@dataclass
class MatchInfo:
    orig_addr: Optional[int]
    recomp_addr: Optional[int]
    name: Optional[str]
    size: Optional[int]
    compare_type: Optional[SymbolType]

    def match_name(self) -> Optional[str]:
        """Combination of the name and compare type.
        Intended for name substitution in the diff. If there is a diff,
        it will be more obvious what this symbol indicates."""
        if self.name is None:
            return None

        ctype = self.compare_type.name if self.compare_type is not None else "UNK"
        name = repr(self.name) if ctype == "STRING" else self.name
        return f"{name} ({ctype})"

    def offset_name(self, ofs: int) -> Optional[str]:
        if self.name is None:
            return None

        return f"{self.name}+{ofs} (OFFSET)"


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


class CompareDb:
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

    def _uid_to_matchinfo(self, uid: UIDType) -> MatchInfo:
        record = self._db[uid]
        return MatchInfo(
            compare_type=record["type"],
            orig_addr=record["orig_addr"],
            recomp_addr=record["recomp_addr"],
            name=record["name"],
            size=record["size"],
        )

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

    def get_unmatched_strings(self) -> Iterator[str]:
        """Return any strings not already identified by STRING markers."""
        for uid, record in self._db.items():
            if record["type"] == SymbolType.STRING and uid not in self._matched_uid:
                yield record["name"]

    def get_all(self) -> Iterator[MatchInfo]:
        """Ordered by orig addr (matched and unmatched).
        Unmatched with recomp addr only appear last, in their order."""
        # Get the uids that have only a recomp_addr
        leftovers = [
            self._tgt2uid[addr]
            for addr in self._tgt_order
            if self._tgt2uid[addr] not in self._matched_uid
        ]
        uids = [*[self._src2uid[addr] for addr in self._src_order], *leftovers]

        for uid in uids:
            yield self._uid_to_matchinfo(uid)

    def get_matches(self) -> Iterator[MatchInfo]:
        for match in self.get_all():
            if match.orig_addr is not None and match.recomp_addr is not None:
                yield match

    def get_one_match(self, addr: int) -> Optional[MatchInfo]:
        """Source addr used. This is for reccmp verbose mode."""
        uid = self._src2uid[addr]
        if uid is not None:
            return self._uid_to_matchinfo(uid)

        return None

    def _get_closest_orig(self, addr: int) -> Optional[int]:
        return self._src_order.prev(addr)

    def _get_closest_recomp(self, addr: int) -> Optional[int]:
        return self._tgt_order.prev(addr)

    def get_by_orig(self, addr: int, exact: bool = True) -> Optional[MatchInfo]:
        uid = self._src2uid.get(addr, None)

        if not exact and uid is None:
            prev = self._get_closest_orig(addr)
            if prev is not None:
                uid = self._src2uid[prev]

        if uid is None:
            return None

        return self._uid_to_matchinfo(uid)

    def get_by_recomp(self, addr: int, exact: bool = True) -> Optional[MatchInfo]:
        uid = self._tgt2uid.get(addr, None)

        if not exact and uid is None:
            prev = self._get_closest_recomp(addr)
            if prev is not None:
                uid = self._tgt2uid[prev]

        if uid is None:
            return None

        return self._uid_to_matchinfo(uid)

    def get_matches_by_type(self, compare_type: SymbolType) -> Iterator[MatchInfo]:
        for match in self.get_matches():
            if match.compare_type == compare_type:
                yield match

    def set_pair(
        self, orig: int, recomp: int, compare_type: Optional[SymbolType] = None
    ) -> bool:
        # todo: create new entry here if neither addr is set?
        if orig in self._src2uid:
            return False

        uid = self._tgt2uid.get(recomp, None)
        if uid is None:
            return False

        self.set_source(uid, orig)
        # TODO: old db forces a clear on the compare type here.
        # This seems odd but we'll preserve it for now.
        # Most consequential in _add_match_in_array where the type is immediately cleared.
        # This is important so we don't try to compare each individual data offset.
        # It also comes into play when checking size of elements with intentional NULL size.
        self.set_type(uid, compare_type)
        return True

    def set_pair_tentative(
        self, orig: int, recomp: int, compare_type: Optional[SymbolType] = None
    ) -> bool:
        """Declare a match for the original and recomp addresses given, but only if:
        1. The original address is not used elsewhere (as with set_pair)
        2. The recomp address has not already been matched
        If the compare_type is given, update this also, but only if NULL in the db.

        The purpose here is to set matches found via some automated analysis
        but to not overwrite a match provided by the human operator."""
        # TODO: I forget why this was necessary
        # Hey I remembered. This is so we don't overwrite symboltype.function in match_imports
        return self.set_pair(orig, recomp, compare_type)

    def set_function_pair(self, orig: int, recomp: int) -> bool:
        """For lineref match or _entry"""
        return self.set_pair(orig, recomp, SymbolType.FUNCTION)

    def create_orig_thunk(self, addr: int, name: str):
        """Create a thunk function reference using the orig address.
        We are here because we have a match on the thunked function,
        but it is not thunked in the recomp build."""

        if addr in self._src2uid:
            return

        thunk_name = f"Thunk of '{name}'"

        # Assuming relative jump instruction for thunks (5 bytes)
        self.set_orig_symbol(addr, SymbolType.FUNCTION, thunk_name, 5)

    def create_recomp_thunk(self, addr: int, name: str):
        """Create a thunk function reference using the recomp address.
        We start from the recomp side for this because we are guaranteed
        to have full information from the PDB. We can use a regular function
        match later to pull in the orig address."""

        if addr in self._tgt2uid:
            return

        thunk_name = f"Thunk of '{name}'"

        # Assuming relative jump instruction for thunks (5 bytes)
        self.set_recomp_symbol(addr, SymbolType.FUNCTION, thunk_name, None, 5)

    def _set_opt_bool(self, addr: int, option: str, enabled: bool = True):
        self._opt[self._src2uid[addr]][option] = enabled

    def mark_stub(self, orig: int):
        self._set_opt_bool(orig, "stub")

    def skip_compare(self, orig: int):
        self._set_opt_bool(orig, "skip")

    def get_match_options(self, addr: int) -> dict[str, Any]:
        return self._opt[self._src2uid[addr]]

    def is_vtordisp(self, recomp_addr: int) -> bool:
        """Check whether this function is a vtordisp based on its
        decorated name. If its demangled name is missing the vtordisp
        indicator, correct that."""
        uid = self._tgt2uid.get(recomp_addr)

        if uid is None:
            return False

        record = self._db[uid]
        if "`vtordisp" in record["name"]:
            return True

        if record["symbol"] is None:
            # happens in debug builds, e.g. for "Thunk of 'LegoAnimActor::ClassName'"
            return False

        new_name = get_vtordisp_name(record["symbol"])
        if new_name is None:
            return False

        self.set_name(uid, new_name)
        return True

    def _find_potential_match(
        self, name: str, compare_type: SymbolType
    ) -> Optional[int]:
        """Name lookup"""
        match_decorate = compare_type != SymbolType.STRING and name.startswith("?")
        if match_decorate:
            uid = self.get_symbol(name)
            if uid is not None and uid not in self._matched_uid:
                record = self._db[uid]
                return record["recomp_addr"]

            return None

        for uid in self.get_name(name):
            if uid in self._matched_uid:
                continue

            record = self._db[uid]
            if record["type"] is None or record["type"] == compare_type:
                return record["recomp_addr"]

        return None

    def _find_static_variable(
        self, variable_name: str, function_sym: str
    ) -> Optional[int]:
        """Get the recomp address of a static function variable.
        Matches using a LIKE clause on the combination of:
        1. The variable name read from decomp marker.
        2. The decorated name of the enclosing function.
        For example, the variable "g_startupDelay" from function "IsleApp::Tick"
        has symbol: `?g_startupDelay@?1??Tick@IsleApp@@QAEXH@Z@4HA`
        The function's decorated name is: `?Tick@IsleApp@@QAEXH@Z`"""
        raise NotImplementedError

    def _match_on(self, compare_type: SymbolType, addr: int, name: str) -> bool:
        # Update the compare_type here too since the marker tells us what we should do

        # Truncate the name to 255 characters. It will not be possible to match a name
        # longer than that because MSVC truncates the debug symbols to this length.
        # See also: warning C4786.
        name = name[:255]

        logger.debug("Looking for %s %s", compare_type.name.lower(), name)
        recomp_addr = self._find_potential_match(name, compare_type)
        if recomp_addr is None:
            return False

        return self.set_pair(addr, recomp_addr, compare_type)

    def get_next_orig_addr(self, addr: int) -> Optional[int]:
        """Return the original address (matched or not) that follows
        the one given. If our recomp function size would cause us to read
        too many bytes for the original function, we can adjust it."""
        return self._src_order.next(addr)

    def match_function(self, addr: int, name: str) -> bool:
        did_match = self._match_on(SymbolType.FUNCTION, addr, name)
        if not did_match:
            logger.error("Failed to find function symbol with name: %s", name)

        return did_match

    def match_vtable(
        self, addr: int, name: str, base_class: Optional[str] = None
    ) -> bool:
        # Set up our potential match names
        bare_vftable = f"{name}::`vftable'"
        for_name = base_class if base_class is not None else name
        for_vftable = f"{name}::`vftable'{{for `{for_name}'}}"

        # Only allow a match against "Class:`vftable'"
        # if this is the derived class.
        if base_class is None or base_class == name:
            uids = [
                *self._name2uids[for_vftable],
                *self._name2uids[bare_vftable],
            ]
        else:
            uids = list(self._name2uids[for_vftable])

        for uid in uids:
            if uid in self._matched_uid:
                continue

            record = self._db[uid]
            return self.set_pair(addr, record["recomp_addr"], SymbolType.VTABLE)

        logger.error("Failed to find vtable for class: %s", name)
        return False

    def match_static_variable(self, addr: int, name: str, function_addr: int) -> bool:
        """Matching a static function variable by combining the variable name
        with the decorated (mangled) name of its parent function."""
        func_uid = self._src2uid.get(function_addr, None)
        if func_uid is None:
            return False

        func = self._db[func_uid]
        if func["symbol"] is None:
            return False

        for _, record in self._db.items():
            if record["symbol"] is None:
                continue

            if (
                record["type"] != SymbolType.FUNCTION
                and name in record["symbol"]
                and func["symbol"] in record["symbol"]
            ):
                return self.set_pair(addr, record["recomp_addr"], SymbolType.DATA)

        return False

    def match_variable(self, addr: int, name: str) -> bool:
        did_match = self._match_on(SymbolType.DATA, addr, name) or self._match_on(
            SymbolType.POINTER, addr, name
        )
        if not did_match:
            logger.error("Failed to find variable: %s", name)

        return did_match

    def match_string(self, addr: int, value: str) -> bool:
        did_match = self._match_on(SymbolType.STRING, addr, value)
        if not did_match:
            escaped = repr(value)
            logger.error("Failed to find string: %s", escaped)

        return did_match
