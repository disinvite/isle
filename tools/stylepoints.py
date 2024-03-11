import re
import argparse
import pathlib
from isledecomp.dir import walk_source_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=pathlib.Path)
    args = parser.parse_args()

    for filename in walk_source_dir(args.source_dir):
        with open(filename, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f):
                if re.match(r"\s*virtual", line) is not None:
                    if re.match(r".*// vtable\+0x[0-9a-f]+\n$", line) is None:
                        print(f"{filename}:{line_no}")
                        print(repr(line))
