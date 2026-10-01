"""OID 2.0 code rendering for the Albi pen.

Port of tools/oid_generator/oid_png_generator.pl by jindroush (MPL 2.0), which is based on
TTT-generatePDF.pl by ernie76 & nomeata from the tip-toi-reveng project. The Python port by
JanValiVales (https://github.com/JanValiVales/Albi_tuzka) was used as a reference.
The output is pixel-identical to the Perl generator (see tests/test_oid.py).

One tile is 32x32 px at 600 dpi (~1.355 mm), one dot is 1 px at 600 dpi; at 1200 dpi everything is
scaled 2x by pixel doubling. The tile must never be resampled to any other scale.

Usage as a tool (same as the Perl generator):
    python -m albik.oid 10000 --size 20 --dpi 1200 -o oid_10000.png
"""
from __future__ import annotations

import argparse
from functools import lru_cache
from importlib import resources

import numpy as np

TILE_PX_600 = 32
DPI_VALUES = (600, 1200)
#same frame pixels and data positions as the Perl generator, (x, y) at 600 dpi
_FRAME = ((0, 0), (8, 0), (16, 0), (24, 0), (0, 8), (1, 16), (0, 24))


@lru_cache(maxsize=1)
def _int2raw() -> np.ndarray:
    data = resources.files("albik").joinpath("data/oid_int2raw.bin").read_bytes()
    return np.frombuffer(data, dtype="<u2")


def raw_code(code: int) -> int:
    """Converts an internal pen code (the number used in bnl.yaml) to the raw code printed on paper."""
    if not 0 <= code <= 0xFFFF:
        raise ValueError(f"code {code} is out of range 0-65535")
    return int(_int2raw()[code])


def _split(value: int) -> list:
    """Splits a raw code into 9 2-bit values: [0] is the checksum, [1]..[8] the bits from MSB to LSB."""
    checksum = (((value >> 2) ^ (value >> 8) ^ (value >> 12) ^ (value >> 14)) & 0x01) << 1
    checksum |= (value ^ (value >> 4) ^ (value >> 6) ^ (value >> 10)) & 0x01
    digits = [checksum]
    for _ in range(8):
        digits.append((value & 0xC000) >> 14)
        value <<= 2
    return digits


def tile(code: int, dpi: int = 1200) -> np.ndarray:
    """Returns one tile of the internal code as a boolean array [y, x], True = black dot."""
    if dpi not in DPI_VALUES:
        raise ValueError(f"dpi must be one of {DPI_VALUES}")
    t = np.zeros((TILE_PX_600, TILE_PX_600), dtype=bool)
    for x, y in _FRAME:
        t[y, x] = True
    for i, d in enumerate(_split(raw_code(code))):
        row = i // 3 + 1
        col = i % 3 + 1
        dx = 1 - 2 * (((d & 0x02) >> 1) ^ (d & 0x01))
        dy = 1 - 2 * ((d & 0x02) >> 1)
        t[row * 8 + dy, col * 8 + dx] = True
    scale = dpi // 600
    return np.kron(t, np.ones((scale, scale), dtype=bool))


def fill(code: int, width: int, height: int, dpi: int = 1200, origin: tuple = (0, 0)) -> np.ndarray:
    """Covers an area of width x height px with the code, as a boolean array [y, x].

    origin is the position of the area's top-left corner on the page in px; the tile grid is anchored at
    the page origin, so neighbouring areas share the same grid.
    """
    t = tile(code, dpi)
    size = t.shape[0]
    ys = (np.arange(height) + origin[1]) % size
    xs = (np.arange(width) + origin[0]) % size
    return t[np.ix_(ys, xs)]


def mm_to_px(mm: float, dpi: int) -> int:
    """Same rounding as the Perl generator."""
    return int(mm / 25.4 * dpi)


def to_image(dots: np.ndarray, dpi: int):
    """Converts a dot array to an RGBA Pillow image (black dots on a transparent background) with dpi set."""
    from PIL import Image

    rgba = np.zeros(dots.shape + (4,), dtype=np.uint8)
    rgba[dots, 3] = 255
    img = Image.fromarray(rgba)
    img.info["dpi"] = (dpi, dpi)
    return img


def main(argv=None):
    p = argparse.ArgumentParser(description="Generates a PNG covered with an OID 2.0 code (internal pen code).")
    p.add_argument("code", type=lambda s: int(s, 0), help="internal code, decimal or 0x hex")
    p.add_argument("--size", type=float, default=20, help="size in mm (default 20)")
    p.add_argument("--size-x", type=float, help="width in mm")
    p.add_argument("--size-y", type=float, help="height in mm")
    p.add_argument("--dpi", type=int, default=1200, choices=DPI_VALUES)
    p.add_argument("-o", "--output", help="output file (default oid_<code>.png)")
    a = p.parse_args(argv)

    w = mm_to_px(a.size_x or a.size, a.dpi)
    h = mm_to_px(a.size_y or a.size, a.dpi)
    out = a.output or f"oid_{a.code}.png"
    to_image(fill(a.code, w, h, a.dpi), a.dpi).save(out, dpi=(a.dpi, a.dpi))
    print(f"written {out} ({w} x {h})")


if __name__ == "__main__":
    main()
