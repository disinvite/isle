"""For subdividing the addresses of a function into code and data
using information from the instructions themselves."""

from typing import Iterator, Optional, Tuple
from enum import Enum


class PartType(Enum):
    CODE = 1
    JUMP = 2
    DATA = 3


class Partition:
    def __init__(
        self, start: int, end: int, cut_type: Optional[PartType] = PartType.CODE
    ) -> None:
        self._cuts = {start: cut_type}
        self._start = start
        self._end = end

    def get_all(self) -> Iterator[Tuple[int, int, PartType]]:
        cuts = sorted(self._cuts.items())
        last = None

        while len(cuts) > 0:
            c = cuts.pop(0)

            # First run
            if last is None:
                last = c

            # If this cut type is different from the last new type
            # OR if it is the same type, but not a CODE cut:
            if (last[1] == c[1] and last[1] != PartType.CODE) or (last[1] != c[1]):
                yield (last[0], c[0] - last[0], last[1])
                last = c

        yield (last[0], self._end - last[0], last[1])

    def _cut(self, addr: int, cut_type: PartType):
        if self._start <= addr < self._end:
            self._cuts[addr] = cut_type

    def cut_code(self, addr: int):
        self._cut(addr, PartType.CODE)

    def cut_jump(self, addr: int):
        self._cut(addr, PartType.JUMP)

    def cut_data(self, addr: int):
        self._cut(addr, PartType.DATA)
