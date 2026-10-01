"""Stable assignment of OID codes to objects and the codes of the pen buttons.

The assignment (object id -> code) is kept in oid_map.yaml. A new object gets the next free code, a removed
object keeps its code, so codes of already printed pages never change.
"""
from __future__ import annotations

from pathlib import Path

import yaml

#object codes, see docs/drawing_to_book/README.md (code ranges)
FIRST_CODE = 10000
LAST_CODE = 49999
BOOK_ID_RANGE = (701, 9999)

#internal codes of the pen buttons, same as SYS_ICONS and MODE_ICONS in tools/creator/bnl_creator.pl
BUTTON_CODES = {
    "volume_up": 0x07,
    "volume_down": 0x08,
    "stop": 0x06,
    "compare": 0x63,
    "mode_1": 0x04,
    "mode_2": 0x05,
    "mode_3": 0x03,
    "mode_4": 0x02,
    "mode_5": 0x01,
    "mode_6": 0x0225,
    "mode_7": 0x0226,
    "mode_8": 0x0227,
    "mode_9": 0x0228,
    "mode_10": 0x0229,
    "mode_11": 0x022A,
    "mode_12": 0x022B,
}


class OidMapError(Exception):
    pass


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for oid_id, code in data.items():
        if not isinstance(code, int) or not FIRST_CODE <= code <= LAST_CODE:
            raise OidMapError(f"{path}: code of '{oid_id}' must be a number {FIRST_CODE}-{LAST_CODE}")
    if len(set(data.values())) != len(data):
        raise OidMapError(f"{path}: the same code is used twice")
    return data


def assign(path: Path, ids: list) -> dict:
    """Returns codes for ids, giving new ids the next free codes and saving the map when it changed."""
    codes = load(path)
    new = [i for i in ids if i not in codes]
    if new:
        nxt = max(codes.values(), default=FIRST_CODE - 1) + 1
        for oid_id in new:
            if nxt > LAST_CODE:
                raise OidMapError(f"no free codes left in {FIRST_CODE}-{LAST_CODE}")
            codes[oid_id] = nxt
            nxt += 1
        path.write_text("#object id -> OID code; keep this file, printed pages depend on it\n"
                        + yaml.safe_dump(codes, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return {i: codes[i] for i in ids}


def button_code(button: str, book_id: int = None) -> int:
    if button == "start":
        if book_id is None:
            raise OidMapError("the drawing has a @start button, the book id is needed")
        if not BOOK_ID_RANGE[0] <= book_id <= BOOK_ID_RANGE[1]:
            raise OidMapError(f"book id {book_id} is out of range {BOOK_ID_RANGE[0]}-{BOOK_ID_RANGE[1]}")
        return book_id
    return BUTTON_CODES[button]
