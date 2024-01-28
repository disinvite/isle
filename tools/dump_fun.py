# Data comparison.

import os
import sys
import argparse
import logging
import re
from typing import List
from struct import unpack, iter_unpack
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from isledecomp.cvdump import Cvdump
from isledecomp.bin import Bin as IsleBin, InvalidVirtualAddressError
from isledecomp.dir import walk_source_dir
from isledecomp.parser.node import ParserVariable

######

kHexChars = '0123456789abcdef'

def binPrint(bin, cols = 16, dataOfs=0, outputFn=print):
    def getByteString(bin):
        return ' '.join([f"{b:02x}" for b in bin])

    def getAsciiString(bin):
        return ''.join([chr(b) if (b < 127 and b > 31) else '.' for b in bin])

    def getLegend():
        return f"        {'  '.join(list(kHexChars))}  {kHexChars}"

    (nRows, remain) = divmod(len(bin), cols)
    if remain > 0:
        nRows += 1

    if cols == 16:
        outputFn(getLegend())

    for i in range(nRows):
        ofs = i * cols
        row = bin[ofs : ofs + cols]
        outputFn(f"{dataOfs + ofs:04x} : {getByteString(row):{3*cols}} {getAsciiString(row)}")

####

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Comparing data values.")
    p.add_argument(
        "recompiled", metavar="recompiled-binary", help="The recompiled binary"
    )
    p.add_argument(
        "pdb", metavar="recompiled-pdb", help="The PDB of the recompiled binary"
    )
    p.add_argument(
        "symbol", metavar="symbol", help="The symbol you want to see"
    )
    p.add_argument(
        "--len", metavar="len", type=int, help="How many bytes to display at whatever address"
    )

    (args, _) = p.parse_known_args()

    if not os.path.isfile(args.recompiled):
        p.error(f"Recompiled binary {args.recompiled} does not exist")

    if not os.path.isfile(args.pdb):
        p.error(f"Symbols PDB {args.pdb} does not exist")

    return args

da = Cs(CS_ARCH_X86, CS_MODE_32)
bracket_regex = re.compile(r"\[(0x\w+)\]")

def print_asm(code, addr, lookup):
    def bracket_replace(m):
        try:
            # Get just the inside of the brackets
            a = int(m.group(1), 16)
            if a in lookup:
                return f"[{lookup[a]}]"
        except Exception:
            pass

        return m.group()

    for i in da.disasm(code, addr):
        # hack sanitize
        if i.op_str.startswith("0x"):
            addr = int(i.op_str, 16)
            if addr in lookup:
                op_str = lookup[addr]
            else:
                # no change
                op_str = i.op_str
        else:
            op_str = bracket_regex.sub(bracket_replace, i.op_str)

        print(f"{i.address:08x}  {i.mnemonic} {op_str}")


def main():
    args = parse_args()
    

    with IsleBin(args.recompiled) as recompfile:
        for sect in recompfile.sections:
            name = sect.name.decode("ascii").rstrip("\x00")
            print(f"{name:8} {sect.virtual_address:08x} {sect.virtual_size:08x} {sect.size_of_raw_data:08}")

        cv = Cvdump(args.pdb).lines().globals().publics().symbols().section_contributions().run()

        lookup = {}
        def load_up(syms):
            for sym in syms:
                try:
                    lookup[recompfile.get_abs_addr(sym.section, sym.offset)] = sym.name
                except IndexError:
                    continue

        load_up(cv.globals)
        load_up(cv.symbols)
        load_up(cv.publics)

        # for k,v in dict(sorted(lookup.items())).items():
        #     print(f"{k:08x} -- {v}")

        contrib_dict = {(s.section, s.offset): s.size for s in cv.sizerefs}

        # We can match on:
        # 1. Name from cvdump/pdb
        # 2. section:offset address
        # 3. 0x... absolute address

        match_addr = None
        match_size = args.len

        # Test for 2
        if ":" in args.symbol and "::" not in args.symbol:
            (section, offset) = args.symbol.split(":", 2)
            try:
                match_addr = recompfile.get_abs_addr(int(section, 16), int(offset, 16))
                print(f"Matching against {match_addr:08x} instead")
                
                # ???
                if match_size is None:
                    match_size = 256

            except ValueError:
                # parse_int failed, never mind
                sys.exit("Could not parse presumed section:offset address.")

        # Test for 1
        if match_addr is None:
            for sym in cv.publics:
                if sym.name == args.symbol:
                    print("match ok")
                    match_addr = recompfile.get_abs_addr(sym.section, sym.offset)
                    match_size = contrib_dict.get((sym.section, sym.offset), 256)
        
        # Test for 3
        if match_addr is None:
            try:
                match_addr = int(args.symbol, 16)
            except ValueError:
                sys.exit("Could not parse presumed absolute address.")

        # hack. need option to show data instead
        raw_data = recompfile.read(match_addr, match_size)
        if args.len is not None:
            binPrint(raw_data)
        else:
            print_asm(raw_data, match_addr, lookup)

if __name__ == "__main__":
    main()
