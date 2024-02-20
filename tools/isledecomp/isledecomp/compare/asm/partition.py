"""For subdividing the addresses of a function into code and data
using information from the instructions themselves."""

from typing import Iterator, NamedTuple, Optional, Tuple
from enum import Enum


class PartType(Enum):
    CODE = 1
    JUMP = 2
    DATA = 3


# TODO: names need some help here.
class PartSlice(NamedTuple):
    addr: int
    size: int
    type: PartType
    index: int


class Partition:
    def __init__(
        self, start: int, end: int, cut_type: Optional[PartType] = PartType.CODE
    ) -> None:
        self._cuts = {start: cut_type}
        self._start = start
        self._end = end

    def _get_cuts_indexed(self) -> Iterator[Tuple[int, PartType, int]]:
        code_counter = 0
        jump_counter = -1
        last_type = None

        for addr, cut_type in self._cuts.items():
            if cut_type == PartType.CODE:
                counter = code_counter
                code_counter += 1
            else:
                if cut_type == PartType.DATA or (
                    cut_type == PartType.JUMP and last_type != PartType.DATA
                ):
                    jump_counter += 1

                counter = jump_counter

            yield (addr, cut_type, counter)
            last_type = cut_type

    def get_all(self) -> Iterator[Tuple[int, int, PartType]]:
        # dict preserves insertion order even if we replace an element. (right?)
        # pairs of data/jump are determined by instruction order,
        # not (necessarily) how the data is ordered.

        cuts = sorted(self._get_cuts_indexed())
        last = None

        while len(cuts) > 0:
            c = cuts.pop(0)

            # First run
            if last is None:
                last = c

            # If this cut type is different from the last new type
            # OR if it is the same type, but not a CODE cut:
            if (last[1] == c[1] and last[1] != PartType.CODE) or (last[1] != c[1]):
                yield PartSlice(last[0], c[0] - last[0], last[1], last[2])
                last = c

        yield PartSlice(last[0], self._end - last[0], last[1], last[2])

    def _cut(self, addr: int, cut_type: PartType):
        if self._start <= addr < self._end:
            self._cuts[addr] = cut_type

    def cut_code(self, addr: int):
        self._cut(addr, PartType.CODE)

    def cut_jump(self, addr: int):
        self._cut(addr, PartType.JUMP)

    def cut_data(self, addr: int):
        self._cut(addr, PartType.DATA)
