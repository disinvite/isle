"""Wrapper for database (here an in-memory sqlite database) that collects the
addresses/symbols that we want to compare between the original and recompiled binaries."""

import logging
from dataclasses import dataclass
from typing import Any, Iterator, List, Optional
from isledecomp.types import SymbolType
from isledecomp.cvdump.demangler import get_vtordisp_name
from .dudu import Nummy, DudyCore


@dataclass
class MatchInfo:
    compare_type: Optional[SymbolType] = None
    orig_addr: Optional[int] = None
    recomp_addr: Optional[int] = None
    name: Optional[str] = None
    size: Optional[int] = None

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


logger = logging.getLogger(__name__)


def nummy_to_matchinfo(nummy: Nummy) -> MatchInfo:
    # todo: meh
    return MatchInfo(
        compare_type=nummy.get("type"),
        orig_addr=nummy.source,
        recomp_addr=nummy.target,
        name=nummy.get("name"),
        size=nummy.get("size"),
    )


class CompareDb:
    # pylint: disable=too-many-public-methods
    def __init__(self):
        self._core = DudyCore()

    def set_orig_symbol(
        self,
        addr: int,
        compare_type: Optional[SymbolType],
        name: Optional[str],
        size: Optional[int],
    ):
        # Ignore collisions here.
        if self._core.orig_used(addr):
            return

        self._core.at_source(addr).set(type=compare_type, name=name, size=size)

    def set_recomp_symbol(
        self,
        addr: int,
        compare_type: Optional[SymbolType],
        name: Optional[str],
        decorated_name: Optional[str],
        size: Optional[int],
    ):
        # Ignore collisions here. The same recomp address can have
        # multiple names (e.g. _strlwr and __strlwr)
        if self._core.recomp_used(addr):
            return

        self._core.at_target(addr).set(
            symbol=decorated_name, type=compare_type, name=name, size=size
        )

    def get_unmatched_strings(self) -> Iterator[str]:
        """Return any strings not already identified by STRING markers."""
        for x in self._core.search_type(SymbolType.STRING, unmatched=True):
            if x.get("name") is not None:
                yield x.get("name")

    def get_all(self) -> Iterator[MatchInfo]:
        for nummy in self._core.all():
            yield nummy_to_matchinfo(nummy)

    def get_matches(self) -> Iterator[MatchInfo]:
        for nummy in self._core.all(matched=True):
            yield nummy_to_matchinfo(nummy)

    def get_one_match(self, addr: int) -> Optional[MatchInfo]:
        nummy = self._core.get(source=addr)
        if nummy is None:
            return None

        return nummy_to_matchinfo(nummy)

    def _get_closest_orig(self, source: int) -> Optional[int]:
        # pylint: disable=protected-access
        # return self._core._sources.prev_or_cur(source)
        try:
            return next(self._core.iter_source(source, reverse=True))
        except StopIteration:
            return None

    def _get_closest_recomp(self, target: int) -> Optional[int]:
        # pylint: disable=protected-access
        # return self._core._targets.prev_or_cur(target)
        try:
            return next(self._core.iter_target(target, reverse=True))
        except StopIteration:
            return None

    def get_by_orig(self, source: int, exact: bool = True) -> Optional[MatchInfo]:
        addr = self._get_closest_orig(source)
        if addr is None or (exact and addr != source):
            return None

        nummy = self._core.get(source=addr)
        if nummy is None:
            return None

        return nummy_to_matchinfo(nummy)

    def get_by_recomp(self, target: int, exact: bool = True) -> Optional[MatchInfo]:
        addr = self._get_closest_recomp(target)
        if addr is None or (exact and addr != target):
            return None

        nummy = self._core.get(target=addr)
        if nummy is None:
            return None

        return nummy_to_matchinfo(nummy)

    def get_matches_by_type(self, compare_type: SymbolType) -> List[MatchInfo]:
        return [
            nummy_to_matchinfo(nummy)
            for nummy in self._core.search_type(compare_type, unmatched=False)
        ]

    def set_pair(
        self, orig: int, recomp: int, compare_type: Optional[SymbolType] = None
    ) -> bool:
        if self._core.orig_used(orig):
            logger.debug("Original address %s not unique!", hex(orig))
            return False

        self._core.at_target(recomp).set(source=orig, type=compare_type)
        return True  # Todo

    def set_pair_tentative(
        self, orig: int, recomp: int, compare_type: Optional[SymbolType] = None
    ) -> bool:
        """Declare a match for the original and recomp addresses given, but only if:
        1. The original address is not used elsewhere (as with set_pair)
        2. The recomp address has not already been matched
        If the compare_type is given, update this also, but only if NULL in the db.

        The purpose here is to set matches found via some automated analysis
        but to not overwrite a match provided by the human operator."""
        if self._core.orig_used(orig):
            # Probable and expected situation. Just ignore it.
            return False

        n = self._core.at_target(recomp)
        n.set(source=orig)

        if n.get("type") is None:
            n.set(type=compare_type)

        return True

    def set_function_pair(self, orig: int, recomp: int) -> bool:
        """For lineref match or _entry"""
        return self.set_pair(orig, recomp, SymbolType.FUNCTION)

    def create_orig_thunk(self, addr: int, name: str) -> bool:
        """Create a thunk function reference using the orig address.
        We are here because we have a match on the thunked function,
        but it is not thunked in the recomp build."""

        if self._core.orig_used(addr):
            return False

        thunk_name = f"Thunk of '{name}'"
        # Assuming relative jump instruction for thunks (5 bytes)
        self._core.at_source(addr).set(
            type=SymbolType.FUNCTION, size=5, name=thunk_name
        )

        return True

    def create_recomp_thunk(self, addr: int, name: str) -> bool:
        """Create a thunk function reference using the recomp address.
        We start from the recomp side for this because we are guaranteed
        to have full information from the PDB. We can use a regular function
        match later to pull in the orig address."""

        if self._core.recomp_used(addr):
            return False

        thunk_name = f"Thunk of '{name}'"
        # Assuming relative jump instruction for thunks (5 bytes)
        self._core.at_target(addr).set(
            type=SymbolType.FUNCTION, size=5, name=thunk_name
        )

        return True

    def mark_stub(self, orig: int):
        self._core.at_source(orig).set(stub=True)

    def skip_compare(self, orig: int):
        self._core.at_source(orig).set(skip=True)

    def get_match_options(self, addr: int) -> Optional[dict[str, Any]]:
        """Todo: remove this. wonky API"""
        n = self._core.get(source=addr)
        return n._extras or {}  # pylint: disable=protected-access

    def is_vtordisp(self, recomp_addr: int) -> bool:
        """Check whether this function is a vtordisp based on its
        decorated name. If its demangled name is missing the vtordisp
        indicator, correct that."""
        func = self._core.get(target=recomp_addr)

        if func is None:
            return False

        if "`vtordisp" in func.get("name"):
            return True

        if func.symbol is None:
            # happens in debug builds, e.g. for "Thunk of 'LegoAnimActor::ClassName'"
            return False

        new_name = get_vtordisp_name(func.symbol)
        if new_name is None:
            return False

        func.set(name=new_name)
        return True

    def _find_potential_match(
        self, name: str, compare_type: SymbolType
    ) -> Optional[int]:
        """Name lookup"""
        match_decorate = compare_type != SymbolType.STRING and name.startswith("?")
        if match_decorate:
            obj = self._core.get(symbol=name)
            if obj is not None and obj.source is None:
                return obj.target

            return None

        for obj in self._core.search_name(name, unmatched=True):
            if obj.get("type") is None or obj.get("type") == compare_type:
                return obj.target

        return None

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
        # pylint: disable=protected-access
        # return self._core._sources.next(addr)
        try:
            return next(self._core.iter_source(addr + 1))
        except StopIteration:
            return None

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

        # Try to match on the "vftable for X first"
        for row in self._core.search_name(for_vftable, unmatched=True):
            return self.set_pair(addr, row.target, SymbolType.VTABLE)

        # Only allow a match against "Class:`vftable'"
        # if this is the derived class.
        if base_class is None or base_class == name:
            for row in self._core.search_name(bare_vftable, unmatched=True):
                return self.set_pair(addr, row.target, SymbolType.VTABLE)

        logger.error("Failed to find vtable for class: %s", name)
        return False

    def match_static_variable(self, addr: int, name: str, function_addr: int) -> bool:
        """Matching a static function variable by combining the variable name
        with the decorated (mangled) name of its parent function."""

        func = self._core.get(source=function_addr)
        if func is None:
            logger.error("No function for static variable: %s", name)
            return False

        # Get the recomp address of a static function variable.
        # Matches using a LIKE clause on the combination of:
        # 1. The variable name read from decomp marker.
        # 2. The decorated name of the enclosing function.
        # For example, the variable "g_startupDelay" from function "IsleApp::Tick"
        # has symbol: `?g_startupDelay@?1??Tick@IsleApp@@QAEXH@Z@4HA`
        # The function's decorated name is: `?Tick@IsleApp@@QAEXH@Z`
        if func.symbol is not None:
            for obj in self._core.search_symbol(func.symbol):
                if (
                    name in obj.symbol
                    and obj.get("type") is None
                    or obj.get("type") == SymbolType.DATA
                ):
                    return self.set_pair(addr, obj.target, SymbolType.DATA)

        logger.error(
            "Failed to match static variable %s from function %s",
            name,
            func.get("name"),
        )

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
