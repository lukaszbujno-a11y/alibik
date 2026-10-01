#!/usr/bin/env python3
"""Regenerates albik/data/oid_int2raw.bin from the table in tools/oid_generator/oid_png_generator.pl.

The Perl generator is the reference; this keeps a single source of truth for the internal -> raw OID table.
The output is 65536 little-endian uint16 values, index = internal pen code, value = raw printed code.
"""
import re
import struct
import sys
from pathlib import Path

GENERATOR = Path(__file__).resolve().parents[1]
PERL_SOURCE = GENERATOR.parent / "tools" / "oid_generator" / "oid_png_generator.pl"
OUTPUT = GENERATOR / "albik" / "data" / "oid_int2raw.bin"


def parse_perl_table(source: str) -> list:
    match = re.search(r"@oid_tbl_int2raw = \((.*?)\);", source, re.S)
    if not match:
        sys.exit(f"table not found in {PERL_SOURCE}")
    table = []
    for item in match.group(1).replace("\n", " ").split(","):
        item = item.strip()
        if not item:
            continue
        if ".." in item:
            start, end = (int(x) for x in item.split(".."))
            table.extend(range(start, end + 1))
        else:
            table.append(int(item))
    return table


def main():
    table = parse_perl_table(PERL_SOURCE.read_text(encoding="utf-8-sig"))
    if len(table) != 65536 or sorted(table) != list(range(65536)):
        sys.exit("table is not a permutation of 0..65535")
    OUTPUT.write_bytes(struct.pack("<65536H", *table))
    print(f"written {OUTPUT} ({len(table)} codes)")


if __name__ == "__main__":
    main()
