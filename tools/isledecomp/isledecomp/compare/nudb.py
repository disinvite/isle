import logging
from typing import Any, Iterator, Optional
from isledecomp.types import SymbolType
from isledecomp.cvdump.demangler import get_vtordisp_name
from .nu_base import UIDType, CompareCore, DbObjectBase

logger = logging.getLogger(__name__)


class MatchInfo(DbObjectBase):
    pass


class CompareDb(CompareCore):
    # pylint: disable=too-many-public-methods
    def _uid_to_matchinfo(self, uid: UIDType) -> MatchInfo:
        return self.get(uid)

    def describe(self, uid: UIDType, offset: int = 0) -> Optional[str]:
        record = self.get(uid)

        if record.name is None:
            return None

        # Check whether the item we have is big enough to contain this offset
        # TODO: How to handle items with null size?
        if record.size is not None and offset >= record.size:
            return None

        # Stringify SymbolType enum
        ctype = record.type.name if record.type is not None else "UNK"

        # repr adds quotes around the string value, which is nice, but the real
        # reason is to escape newlines; they will break asm sanitize.
        name = repr(record.name) if ctype == "STRING" else record.name
        if offset == 0:
            return f"{name} ({ctype})"

        if record.type == SymbolType.DATA:
            return f"{name}+{offset} (OFFSET)"

        return None

    def describe_orig(self, addr: int, exact: bool):
        actual = self._src2uid.prev_or_cur(addr)
        if actual is None:
            return None

        if exact and actual != addr:
            return None

        uid = self.get_source(actual)
        assert uid is not None  # todo
        return self.describe(uid, addr - actual)

    def describe_recomp(self, addr: int, exact: bool):
        actual = self._tgt2uid.prev_or_cur(addr)
        if actual is None:
            return None

        if exact and actual != addr:
            return None

        uid = self.get_target(actual)
        assert uid is not None  # todo
        return self.describe(uid, addr - actual)

    def get_unmatched_strings(self) -> Iterator[str]:
        """Return any strings not already identified by STRING markers."""
        for uid in self.get_type(SymbolType.STRING):
            if uid not in self._matched_uid:
                record = self.get(uid)
                yield record.name

    def get_all(self) -> Iterator[MatchInfo]:
        """Ordered by orig addr (matched and unmatched).
        Unmatched with recomp addr only appear last, in their order."""
        for uid in self.in_order():
            yield self._uid_to_matchinfo(uid)

    def get_matches(self) -> Iterator[MatchInfo]:
        for uid in self.in_order(matched_only=True):
            yield self._uid_to_matchinfo(uid)

    def get_one_match(self, addr: int) -> Optional[MatchInfo]:
        """Source addr used. This is for reccmp verbose mode."""
        uid = self.get_source(addr)
        if uid is not None:
            return self._uid_to_matchinfo(uid)

        return None

    def _get_closest_orig(self, addr: int) -> Optional[int]:
        return self._src2uid.prev(addr)

    def _get_closest_recomp(self, addr: int) -> Optional[int]:
        return self._tgt2uid.prev(addr)

    def get_by_orig(self, addr: int, exact: bool = True) -> Optional[MatchInfo]:
        uid = self._src2uid.get(addr)

        if not exact and uid is None:
            prev = self._get_closest_orig(addr)
            if prev is not None:
                uid = self._src2uid[prev]

        if uid is None:
            return None

        return self._uid_to_matchinfo(uid)

    def get_by_recomp(self, addr: int, exact: bool = True) -> Optional[MatchInfo]:
        uid = self._tgt2uid.get(addr)

        if not exact and uid is None:
            prev = self._get_closest_recomp(addr)
            if prev is not None:
                uid = self._tgt2uid[prev]

        if uid is None:
            return None

        return self._uid_to_matchinfo(uid)

    def get_matches_by_type(self, compare_type: SymbolType) -> Iterator[MatchInfo]:
        for match in self.get_matches():
            if match.type == compare_type:
                yield match

    def set_pair(
        self, orig: int, recomp: int, compare_type: Optional[SymbolType] = None
    ) -> bool:
        # todo: create new entry here if neither addr is set?
        if orig in self._src2uid:
            return False

        uid = self._tgt2uid.get(recomp)
        if uid is None:
            return False

        record = self.get(uid)
        record.orig_addr = orig

        # TODO: old db forces a clear on the compare type here.
        # This seems odd but we'll preserve it for now.
        # Most consequential in _add_match_in_array where the type is immediately cleared.
        # This is important so we don't try to compare each individual data offset.
        # It also comes into play when checking size of elements with intentional NULL size.
        record.type = compare_type
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

        record = self.get(uid)
        if "`vtordisp" in record.name:
            return True

        if record.symbol is None:
            # happens in debug builds, e.g. for "Thunk of 'LegoAnimActor::ClassName'"
            return False

        new_name = get_vtordisp_name(record.symbol)
        if new_name is None:
            return False

        record.name = new_name
        return True

    def _find_potential_match(
        self, name: str, compare_type: SymbolType
    ) -> Optional[DbObjectBase]:
        """Name lookup"""
        match_decorate = compare_type != SymbolType.STRING and name.startswith("?")
        if match_decorate:
            uid = self.get_symbol(name)
            if uid is not None and uid not in self._matched_uid:
                return self.get(uid)

            return None

        for uid in self.get_name(name):
            if uid in self._matched_uid:
                continue

            record = self.get(uid)
            if record.type is None or record.type == compare_type:
                return record

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
        record = self._find_potential_match(name, compare_type)
        if record is None:
            return False

        record.orig_addr = addr
        record.type = compare_type
        return True

    def get_next_orig_addr(self, addr: int) -> Optional[int]:
        """Return the original address (matched or not) that follows
        the one given. If our recomp function size would cause us to read
        too many bytes for the original function, we can adjust it."""
        return self._src2uid.next(addr)

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

            record = self.get(uid)
            record.orig_addr = addr
            record.type = SymbolType.VTABLE
            return True

        logger.error("Failed to find vtable for class: %s", name)
        return False

    def match_static_variable(self, addr: int, name: str, function_addr: int) -> bool:
        """Matching a static function variable by combining the variable name
        with the decorated (mangled) name of its parent function."""
        func_uid = self._src2uid.get(function_addr)
        if func_uid is None:
            return False

        func = self.get(func_uid)
        if func.symbol is None:
            return False

        for record in self.items():  # TODO: better method here
            if record.symbol is None:
                continue

            if (
                record.type != SymbolType.FUNCTION
                and name in record.symbol
                and func.symbol in record.symbol
            ):
                record.orig_addr = addr
                record.type = SymbolType.DATA
                return True

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
