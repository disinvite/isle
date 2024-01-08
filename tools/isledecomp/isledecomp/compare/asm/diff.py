# TODO: rewrite
"""Text formatting for x86 machine code, with the end goal of comparing the assembly.
We are using the capstone library for bytes-to-asm conversion. The actual comparison
happens later by comparing the assembly text, using the longest common subsequence
(LCS) provided by python difflib.
Therefore, the goal of this module is to produce assembly text that will match
irrespective of virtual address differences between the two code blocks."""

import re
from typing import Callable, Optional
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

disassembler = Cs(CS_ARCH_X86, CS_MODE_32)

ptr_replace_regex = re.compile(r"ptr \[(0x\w+)\]")


def _default_should_replace(_: int) -> bool:
    return False


def _default_replace_name(addr: int) -> str:
    return hex(addr)


def _default_replace_value(addr: int, _) -> str:
    return hex(addr)


def sanitize(
    mnemonic: str,
    op_str: str,
    should_replace: Callable[[int], bool] = _default_should_replace,
    replace_with_name: Callable[[int], str] = _default_replace_name,
):
    # TODO: replace_with_value: Callable[[int, int], str] = _default_replace_value,
    if len(op_str) == 0:
        return (mnemonic, None)

    if mnemonic in ["call", "jmp"]:
        # Filter out "calls" because the offsets we're not currently trying to
        # match offsets. As long as there's a call in the right place, it's
        # probably accurate.
        try:
            addr = int(op_str, 16)
        except ValueError:
            pass
        else:
            op_str = replace_with_name(addr)

        return (mnemonic, op_str)

    def filter_out_ptr(match):
        try:
            offset = int(match.group(1), 16)
            placeholder = replace_with_name(offset)
            return f"ptr [{placeholder}]"
        except ValueError:
            # Return the string with no changes
            return match.group(0)

    op_str = ptr_replace_regex.sub(filter_out_ptr, op_str)

    # Use heuristics to filter out any args that look like offsets
    words = op_str.split(" ")
    for i, word in enumerate(words):
        try:
            inttest = int(word, 16)
            if should_replace(inttest):
                words[i] = replace_with_name(inttest)
        except ValueError:
            pass
    op_str = " ".join(words)

    return mnemonic, op_str


class OffsetPlaceholderGenerator:
    def __init__(self):
        self.counter = 0
        self.replacements = {}

    def bump(self):
        """Tick the counter up by one if we found the name without using a placeholder.
        This is so the OFFSET numbers will still match."""
        self.counter += 1

    def get(self, replace_addr):
        if replace_addr in self.replacements:
            return self.replacements[replace_addr]
        self.counter += 1
        replacement = f"<OFFSET{self.counter}>"
        self.replacements[replace_addr] = replacement
        return replacement


def parse_asm(file, data, name_lookup: Optional[Callable[[int], str]] = None):
    asm = []
    placeholder_generator = OffsetPlaceholderGenerator()

    def should_replace(addr: int) -> bool:
        return file.is_relocated_addr(addr)

    def replace_with_name(addr: int) -> str:
        if name_lookup is not None:
            name = name_lookup(addr)
            if name is not None:
                placeholder_generator.bump()
                return name

        return placeholder_generator.get(addr)

    for _, __, _mnemonic, _op_str in disassembler.disasm_lite(data, 0):
        # Use heuristics to disregard some differences that aren't representative
        # of the accuracy of a function (e.g. global offsets)
        mnemonic, op_str = sanitize(
            _mnemonic, _op_str, should_replace, replace_with_name
        )
        if op_str is None:
            asm.append(mnemonic)
        else:
            asm.append(f"{mnemonic} {op_str}")
    return asm
