"""Converts x86 machine code into text (i.e. assembly). The end goal is to
compare the code in the original and recomp binaries, using longest common
subsequence (LCS), i.e. difflib.SequenceMatcher.
The capstone library takes the raw bytes and gives us the mnemonic
and operand(s) for each instruction. We need to "sanitize" the text further
so that virtual addresses are replaced by symbol name or a generic
placeholder string."""

import re
import struct
from functools import cache
from typing import Callable, List, Optional, Tuple
from collections import namedtuple
from isledecomp.bin import InvalidVirtualAddressError
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .partition import Partition, PartType

disassembler = Cs(CS_ARCH_X86, CS_MODE_32)

ptr_replace_regex = re.compile(r"(?P<data_size>\w+) ptr \[(?P<addr>0x[0-9a-fA-F]+)\]")

array_index_regex = re.compile(
    r"(?P<data_size>\w+) ptr \[[\w\*]+ \+ (?P<addr>0x[0-9a-fA-F]+)\]"
)

DisasmLiteInst = namedtuple("DisasmLiteInst", "address, size, mnemonic, op_str")


@cache
def from_hex(string: str) -> Optional[int]:
    try:
        return int(string, 16)
    except ValueError:
        pass

    return None


def get_float_size(size_str: str) -> int:
    return 8 if size_str == "qword" else 4


class ParseAsm:
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        relocate_lookup: Optional[Callable[[int], bool]] = None,
        name_lookup: Optional[Callable[[int], str]] = None,
        float_lookup: Optional[Callable[[int, int], Optional[str]]] = None,
    ) -> None:
        self.relocate_lookup = relocate_lookup
        self.name_lookup = name_lookup
        self.float_lookup = float_lookup
        self.replacements = {}
        self.number_placeholders = True

        # If we did not detect a jump/data table in our first pass
        # we can skip some processing steps.
        self.found_jump_table = False

        # Mapping of address and label name we need to place down before
        # the instruction at said address. Obtained by reading jump tables.
        self.labels = {}

        # Partition of the addresses in this function.
        # TODO: should construct here instead
        self.partition = None

    def reset(self):
        self.replacements = {}

    def is_relocated(self, addr: int) -> bool:
        if callable(self.relocate_lookup):
            return self.relocate_lookup(addr)

        return False

    def float_replace(self, addr: int, data_size: int) -> Optional[str]:
        if callable(self.float_lookup):
            try:
                float_str = self.float_lookup(addr, data_size)
            except InvalidVirtualAddressError:
                # probably caused by reading an invalid instruction
                return None
            if float_str is not None:
                return f"{float_str} (FLOAT)"

        return None

    def lookup(self, addr: int) -> Optional[str]:
        """Return a replacement name for this address if we find one."""
        if (cached := self.replacements.get(addr, None)) is not None:
            return cached

        if callable(self.name_lookup):
            if (name := self.name_lookup(addr)) is not None:
                self.replacements[addr] = name
                return name

        return None

    def replace(self, addr: int) -> str:
        """Same function as lookup above, but here we return a placeholder
        if there is no better name to use."""
        if (name := self.lookup(addr)) is not None:
            return name

        # The placeholder number corresponds to the number of addresses we have
        # already replaced. This is so the number will be consistent across the diff
        # if we can replace some symbols with actual names in recomp but not orig.
        idx = len(self.replacements) + 1
        placeholder = f"<OFFSET{idx}>" if self.number_placeholders else "<OFFSET>"
        self.replacements[addr] = placeholder
        return placeholder

    def read_jump_table(self, data: bytes, table_index: int = 0):
        # TODO: assert len(data) % 4 == 0
        data_size = len(data)
        if data_size % 4 != 0:
            data_size = 4 * (data_size // 4)
            data = data[:data_size]

        for i, (addr,) in enumerate(struct.iter_unpack("<L", data)):
            self.labels[addr] = f".switch_{table_index}_case_{i}"

    def sanitize_jump_table(self, data: bytes) -> List[str]:
        # TODO: assert len(data) % 4 == 0
        data_size = len(data)
        if data_size % 4 != 0:
            data_size = 4 * (data_size // 4)
            data = data[:data_size]

        return [
            self.labels.get(addr, "PLACEHOLDER")
            for (addr,) in struct.iter_unpack("<L", data)
        ]

    def sanitize_switch_data(self, data: bytes) -> List[str]:
        return [hex(b) for b in data]

    def first_pass(self, inst: DisasmLiteInst, start: int, end: int) -> int:
        """Read an instruction from the function and identify any jump tables
        or data segments within the boundary of the function.
        Both are associated with switch statements.
        If we find either one, return the address that it points to.
        The goal here is to establish the "end of code" so that we do not
        read bogus instructions from a section that has data.
        NOTE: This makes a big assumption that we will not have a function
        where there is code followed by a jump table (and data) followed
        by more code in the same function.
        """

        # TODO: can we do any meaningful analysis if we don't know
        # how big the function is?
        if start >= end:
            return end

        # We are only watching these instructons in search of
        # switch data or jump tables.
        if inst.mnemonic not in ("mov", "jmp"):
            return end

        # The instruction of interest is either:
        # - mov al, byte ptr [reg + addr]
        # - jmp dword ptr [reg*0x4 + addr]
        # In both cases we want the last operand.
        operand = inst.op_str.split(", ", 1)[-1]

        # Try to match the address of the array
        match = array_index_regex.match(operand)
        if match is None:
            return end

        array_addr = from_hex(match["addr"])
        if array_addr is None:
            return end

        # If the address is not inside the bounds of the function, return.
        # This should exclude an index into an array from a global variable.
        if not start <= array_addr < end:
            return end

        self.found_jump_table = True

        if inst.mnemonic == "mov":
            self.partition.cut_data(array_addr)

        if inst.mnemonic == "jmp":
            self.partition.cut_jump(array_addr)

        return array_addr

    def sanitize(self, inst: DisasmLiteInst) -> Tuple[str, str]:
        if len(inst.op_str) == 0:
            # Nothing to sanitize
            return (inst.mnemonic, "")

        if "0x" not in inst.op_str:
            return (inst.mnemonic, inst.op_str)

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
                return (inst.mnemonic, self.replace(op_str_address))

            if inst.mnemonic == "jmp":
                # The unwind section contains JMPs to other functions.
                # If we have a name for this address, use it. If not,
                # do not create a new placeholder. We will instead
                # fall through to generic jump handling below.
                potential_name = self.lookup(op_str_address)
                if potential_name is not None:
                    return (inst.mnemonic, potential_name)

            if inst.mnemonic.startswith("j"):
                # i.e. if this is any jump
                # Show the jump offset rather than the absolute address
                jump_displacement = op_str_address - (inst.address + inst.size)
                return (inst.mnemonic, hex(jump_displacement))

        def filter_out_ptr(match):
            """Helper for re.sub, see below"""
            offset = from_hex(match.group("addr"))

            if offset is not None:
                # We assume this is always an address to replace
                placeholder = self.replace(offset)
                return f'{match.group("data_size")} ptr [{placeholder}]'

            # Strict regex should ensure we can read the hex number.
            # But just in case: return the string with no changes
            return match.group(0)

        def float_ptr_replace(match):
            offset = from_hex(match.group("addr"))

            if offset is not None:
                # If we can find a variable name for this pointer, use it.
                placeholder = self.lookup(offset)

                # Read what's under the pointer and show the decimal value.
                if placeholder is None:
                    placeholder = self.float_replace(
                        offset, get_float_size(match.group("data_size"))
                    )

                # If we can't read the float, use a regular placeholder.
                if placeholder is None:
                    placeholder = self.replace(offset)

                return f'{match.group("data_size")} ptr [{placeholder}]'

            # Strict regex should ensure we can read the hex number.
            # But just in case: return the string with no changes
            return match.group(0)

        if inst.mnemonic.startswith("f"):
            # If floating point instruction
            op_str = ptr_replace_regex.sub(float_ptr_replace, inst.op_str)
        else:
            op_str = ptr_replace_regex.sub(filter_out_ptr, inst.op_str)

        def replace_immediate(chunk: str) -> str:
            if (inttest := from_hex(chunk)) is not None:
                # If this value is a virtual address, it is referenced absolutely,
                # which means it must be in the relocation table.
                if self.is_relocated(inttest):
                    return self.replace(inttest)

            return chunk

        # Performance hack:
        # Skip this step if there is nothing left to consider replacing.
        if "0x" in op_str:
            # Replace immediate values with name or placeholder (where appropriate)
            op_str = ", ".join(map(replace_immediate, op_str.split(", ")))

        return inst.mnemonic, op_str

    def parse_asm(self, data: bytes, start_addr: Optional[int] = 0) -> List[str]:
        asm = []

        # Grab it here because we will read it twice
        instructions = [
            DisasmLiteInst(*inst) for inst in disassembler.disasm_lite(data, start_addr)
        ]

        end_addr = start_addr + len(data)
        self.partition = Partition(start_addr, end_addr)

        end_of_code = end_addr

        # PASS 1: Scanning for jump tables
        for inst in instructions:
            # Don't read junk instructions from a jump or data table.
            if inst.address >= end_of_code:
                break

            reported_end = self.first_pass(inst, start_addr, end_addr)
            end_of_code = min(end_of_code, reported_end)

        if self.found_jump_table:
            # We now have to read the jump table(s).
            jump_table_index = 0
            for p_start, p_size, p_type in self.partition.get_all():
                if p_type == PartType.DATA:
                    self.labels[p_start] = f".switch_data_{jump_table_index}"

                if p_type == PartType.JUMP:
                    self.labels[p_start] = f".jump_table_{jump_table_index}"
                    # TODO: cleaner way to convert v.addr back to offset.
                    self.read_jump_table(
                        data[p_start - start_addr : p_start - start_addr + p_size],
                        jump_table_index,
                    )
                    jump_table_index += 1

        # PASS 2: Sanitize and stringify
        code_was_read = False
        for p_start, p_size, p_type in self.partition.get_all():
            if p_type == PartType.CODE and not code_was_read:
                code_was_read = True

                # TODO: This is a hack because we are using the
                # already read instructions from disasm_lite to save time.
                # This won't work if the CODE section is not first and
                # if there is more than one.
                for inst in instructions:
                    if inst.address >= end_of_code:
                        break

                    # Use heuristics to disregard some differences that aren't representative
                    # of the accuracy of a function (e.g. global offsets)
                    result = self.sanitize(inst)

                    # If a switch case jumps to this address, show the label
                    if self.found_jump_table and inst.address in self.labels:
                        asm.append(self.labels[inst.address])

                    # mnemonic + " " + op_str
                    asm.append(" ".join(result))

            else:
                if p_start in self.labels:
                    asm.append(self.labels[p_start])

                data_slice = data[p_start - start_addr : p_start - start_addr + p_size]
                if p_type == PartType.JUMP:
                    for line in self.sanitize_jump_table(data_slice):
                        asm.append(line)

                if p_type == PartType.DATA:
                    for line in self.sanitize_switch_data(data_slice):
                        asm.append(line)

        return asm
