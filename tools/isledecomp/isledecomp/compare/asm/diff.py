"""Converts x86 machine code into text (i.e. assembly). The end goal is to
compare the code in the original and recomp binaries, using longest common
subsequence (LCS), i.e. difflib.SequenceMatcher.
The capstone library takes the raw bytes and gives us the mnemnonic
and operand(s) for each instruction. We need to "sanitize" the text further
so that virtual addresses are replaced by symbol name or a generic
placeholder string."""

import re
from typing import Callable, Optional
from collections import namedtuple
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

disassembler = Cs(CS_ARCH_X86, CS_MODE_32)

ptr_replace_regex = re.compile(r"ptr \[(0x\w+)\]")

DisasmLiteInst = namedtuple("DisasmLiteInst", "address, size, mnemonic, op_str")


def _default_should_replace(_: int) -> bool:
    return False


def _default_replace_name(addr: int, _: bool) -> str:
    return hex(addr)


def from_hex(string: str) -> Optional[int]:
    try:
        return int(string, 16)
    except ValueError:
        pass

    return None


def sanitize(
    inst: DisasmLiteInst,
    should_replace: Callable[[int], bool] = _default_should_replace,
    replace_with_name: Callable[[int, bool], str] = _default_replace_name,
):
    if len(inst.op_str) == 0:
        # Nothing to sanitize
        return (inst.mnemonic, "")

    # For jumps or calls, if the entire op_str is a hex number, the value
    # is a relative offset.
    # Otherwise (i.e. it looks like `dword ptr [address]`) it is an
    # absolute indirect that we will handle below.
    # Providing the starting address of the function to capstone.disasm has
    # automatically resolved relative offsets to an absolute address.
    # We will have to undo this for some of the jumps or they will not match.
    op_str_address = from_hex(inst.op_str)

    if op_str_address is not None:
        if inst.mnemonic == "call":
            return (inst.mnemonic, replace_with_name(op_str_address))

        if inst.mnemonic == "jmp":
            # The unwind section contains JMPs to other functions.
            # If we have a name for this address, use it. If not,
            # do not create a new placeholder. We will instead
            # fall through to generic jump handling below.
            potential_name = replace_with_name(op_str_address, False)
            if potential_name is not None:
                return (inst.mnemonic, potential_name)

        if inst.mnemonic.startswith("j"):
            # i.e. if this is any jump
            # Show the jump offset rather than the absolute address
            jump_displacement = op_str_address - (inst.address + inst.size)
            return (inst.mnemonic, hex(jump_displacement))

    def filter_out_ptr(match):
        """Helper for re.sub, see below"""
        offset = from_hex(match.group(1))

        if offset is not None:
            # We assume this is always an address to replace
            placeholder = replace_with_name(offset)
            return f"ptr [{placeholder}]"

        # Return the string with no changes
        return match.group(0)

    op_str = ptr_replace_regex.sub(filter_out_ptr, inst.op_str)

    # Performance hack:
    # Skip this step if there is nothing left to consider replacing.
    if "0x" in op_str:
        # Replace immediate values with name or placeholder (where appropriate)
        words = op_str.split(", ")
        for i, word in enumerate(words):
            try:
                inttest = int(word, 16)
                # If this value is a virtual address, it is referenced absolutely,
                # which means it must be in the relocation table.
                if should_replace(inttest):
                    words[i] = replace_with_name(inttest)
            except ValueError:
                pass
        op_str = ", ".join(words)

    return inst.mnemonic, op_str


class OffsetPlaceholderGenerator:
    def __init__(self):
        self.counter = 0
        self.replacements = {}

    def set(self, addr: int, name: str):
        self.replacements[addr] = name
        self.counter += 1

    def get(self, addr: int) -> Optional[str]:
        return self.replacements.get(addr, None)

    def create(self, addr: int) -> str:
        if (cached := self.get(addr)) is not None:
            return cached

        self.counter += 1
        replacement = f"<OFFSET{self.counter}>"
        self.replacements[addr] = replacement
        return replacement


def parse_asm(
    data: bytes,
    start_addr: Optional[int] = 0,
    should_replace: Callable[[int], bool] = _default_should_replace,
    name_lookup: Optional[Callable[[int], str]] = None,
):
    asm = []
    placeholder_generator = OffsetPlaceholderGenerator()

    def replace_with_name(addr: int, use_placeholder: bool = True) -> str:
        # Use cached value if we have it
        if (name := placeholder_generator.get(addr)) is not None:
            return name

        # Look up symbol name if that option is available
        if name_lookup is not None:
            name = name_lookup(addr)
            if name is not None:
                placeholder_generator.set(addr, name)
                return name

        # Escape hatch for replacements on the JMP instruction.
        # If we cannot find the symbol name, assume it is a "local" jump
        if not use_placeholder:
            return None

        # Else create a new placeholder
        return placeholder_generator.create(addr)

    for inst in disassembler.disasm_lite(data, start_addr):
        # Use heuristics to disregard some differences that aren't representative
        # of the accuracy of a function (e.g. global offsets)
        result = sanitize(DisasmLiteInst(*inst), should_replace, replace_with_name)
        # mnemonic + " " + op_str
        asm.append(" ".join(result))
    return asm
