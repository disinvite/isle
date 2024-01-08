# TODO: rewrite
"""Text formatting for x86 machine code, with the end goal of comparing the assembly.
We are using the capstone library for bytes-to-asm conversion. The actual comparison
happens later by comparing the assembly text, using the longest common subsequence
(LCS) provided by python difflib.
Therefore, the goal of this module is to produce assembly text that will match
irrespective of virtual address differences between the two code blocks."""

import re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

disassembler = Cs(CS_ARCH_X86, CS_MODE_32)

ptr_replace_regex = re.compile(r"ptr \[(0x\w+)\]")


def sanitize(file, placeholder_generator, mnemonic, op_str):
    op_str_is_number = False
    try:
        int(op_str, 16)
        op_str_is_number = True
    except ValueError:
        pass

    if (mnemonic in ["call", "jmp"]) and op_str_is_number:
        # Filter out "calls" because the offsets we're not currently trying to
        # match offsets. As long as there's a call in the right place, it's
        # probably accurate.
        op_str = placeholder_generator.get(int(op_str, 16))
    else:

        def filter_out_ptr(match):
            try:
                offset = int(match.group(1), 16)
                placeholder = placeholder_generator.get(offset)
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
                if file.is_relocated_addr(inttest):
                    words[i] = placeholder_generator.get(inttest)
            except ValueError:
                pass
        op_str = " ".join(words)

    return mnemonic, op_str


class OffsetPlaceholderGenerator:
    def __init__(self):
        self.counter = 0
        self.replacements = {}

    def get(self, replace_addr):
        if replace_addr in self.replacements:
            return self.replacements[replace_addr]
        self.counter += 1
        replacement = f"<OFFSET{self.counter}>"
        self.replacements[replace_addr] = replacement
        return replacement


def parse_asm(file, data):
    asm = []
    placeholder_generator = OffsetPlaceholderGenerator()
    for _, __, _mnemonic, _op_str in disassembler.disasm_lite(data, 0):
        # Use heuristics to disregard some differences that aren't representative
        # of the accuracy of a function (e.g. global offsets)
        mnemonic, op_str = sanitize(file, placeholder_generator, _mnemonic, _op_str)
        if op_str is None:
            asm.append(mnemonic)
        else:
            asm.append(f"{mnemonic} {op_str}")
    return asm
