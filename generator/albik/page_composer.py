"""Composes the printable page: the drawing with OID codes laid over its objects.

The artwork is rendered from the SVG by Inkscape at the printer resolution, lightened under coded objects,
and every object mask (from svg_import) is filled with the dots of its code. The code grid is anchored at the
page origin and never scaled. The result is one raster written 1:1 into a PDF of the page size.

Usage:
    python -m albik.page_composer drawing.svg --objects build/objects.yaml --book-id 8000 -o build/page.pdf
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import img2pdf
import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

from albik import oid, oid_map
from albik.svg_import import PREVIEW_FONTS, inkscape_binary

#artwork under codes keeps only this fraction of its darkness (same as test/my-book/make_page.pl)
LIGHTEN = 0.4
#calibration ruler: 100 mm long, placed this far from the bottom-left corner of the page
RULER_MM = 100
RULER_POS_MM = (15, 10)
#rows processed at once, keeps memory low at 1200 dpi
STRIP_ROWS = 1024
PREVIEW_DPI = 100  # must divide 600 and 1200

Image.MAX_IMAGE_PIXELS = None


class ComposeError(Exception):
    pass


def render_artwork(svg: Path, dpi: int, tmp: Path) -> Image.Image:
    out = tmp / "art.png"
    actions = ["export-type:png", f"export-dpi:{dpi}", "export-area-page", "export-background:white",
               "export-background-opacity:1", "export-png-color-mode:RGB_8", f"export-filename:{out}", "export-do"]
    r = subprocess.run([inkscape_binary(), str(svg), "--actions=" + ";".join(actions)], capture_output=True, text=True)
    if r.returncode != 0 or not out.exists():
        raise ComposeError("Inkscape export failed:\n" + r.stderr)
    return Image.open(out).convert("RGB")


def load_areas(objects_yaml: Path, oid_map_path: Path, book_id: int) -> tuple:
    """Returns ([(name, code, mask)] for all objects and buttons, page info) from objects.yaml."""
    data = yaml.safe_load(objects_yaml.read_text(encoding="utf-8"))
    base = objects_yaml.parent
    codes = oid_map.assign(oid_map_path, [o["id"] for o in data["objects"]])
    areas = []
    for o in data["objects"]:
        areas.append((o["label"], codes[o["id"]], base / o["mask"]))
    for b in data["buttons"]:
        areas.append(("@" + b["id"], oid_map.button_code(b["id"], book_id), base / b["mask"]))
    return [(name, code, np.array(Image.open(mask)) > 0) for name, code, mask in areas], data["page"]


def draw_ruler(img: Image.Image, dpi: int) -> tuple:
    """Draws a 100 mm line with 10 mm ticks; returns its box (x0, y0, x1, y1) in px."""
    px = dpi / 25.4
    h = img.height
    x0 = int(RULER_POS_MM[0] * px)
    y = int(h - RULER_POS_MM[1] * px)
    x1 = x0 + int(round(RULER_MM * px))
    draw = ImageDraw.Draw(img)
    width = max(int(0.3 * px), 1)
    draw.rectangle((x0, y - width // 2, x1, y + width // 2), fill="black")
    for i in range(0, RULER_MM + 1, 10):
        x = x0 + int(round(i * px))
        tick = 3 * px if i % 50 == 0 else 1.5 * px
        draw.rectangle((x - width // 2, int(y - tick), x + width // 2, y), fill="black")
    font_file = next((f for f in PREVIEW_FONTS if Path(f).exists()), None)
    font = ImageFont.truetype(font_file, int(2.5 * px)) if font_file else ImageFont.load_default()
    draw.text((x1 + 2 * px, y), "100 mm", fill="black", font=font, anchor="lm")
    return x0, int(y - 3 * px), x1 + int(20 * px), int(y + width)


def compose(svg: Path, objects_yaml: Path, out_pdf: Path, oid_map_path: Path, book_id: int = None,
            dpi: int = 1200, lighten: float = LIGHTEN, ruler: bool = True, png: Path = None) -> dict:
    if dpi not in oid.DPI_VALUES:
        raise ComposeError(f"dpi must be one of {oid.DPI_VALUES}")
    areas, page_info = load_areas(objects_yaml, oid_map_path, book_id)
    with tempfile.TemporaryDirectory() as tmp:
        art = render_artwork(svg, dpi, Path(tmp))
    ruler_box = draw_ruler(art, dpi) if ruler else None
    page = np.array(art)
    del art
    h, w = page.shape[:2]
    warnings = []

    #art pixel -> mask pixel (masks have a lower resolution, nearest neighbour without interpolation)
    mask_dpi = page_info["mask_dpi"]
    mh, mw = areas[0][2].shape if areas else (0, 0)
    mx = np.minimum(np.arange(w) * mask_dpi // dpi, mw - 1)
    lut = np.array([int(255 - (255 - v) * lighten + 0.5) for v in range(256)], dtype=np.uint8)

    for y0 in range(0, h, STRIP_ROWS):
        y1 = min(y0 + STRIP_ROWS, h)
        my = np.minimum(np.arange(y0, y1) * mask_dpi // dpi, mh - 1)
        strip = page[y0:y1]
        coded = np.zeros((y1 - y0, w), dtype=bool)
        dots = np.zeros((y1 - y0, w), dtype=bool)
        for _, code, mask in areas:
            m = mask[np.ix_(my, mx)]
            if not m.any():
                continue
            coded |= m
            dots |= m & oid.fill(code, w, y1 - y0, dpi, origin=(0, y0))
        strip[coded] = lut[strip[coded]]
        strip[dots] = 0

    if ruler_box:
        x0, ry0, x1, ry1 = ruler_box
        for name, _, mask in areas:
            sub = mask[ry0 * mask_dpi // dpi:ry1 * mask_dpi // dpi + 1, x0 * mask_dpi // dpi:x1 * mask_dpi // dpi + 1]
            if sub.any():
                warnings.append(f"'{name}' overlaps the calibration ruler at the bottom of the page")

    img = Image.fromarray(page)
    del page
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    preview = out_pdf.with_name(out_pdf.stem + "_preview.png")
    img.reduce(dpi // PREVIEW_DPI).save(preview)
    with tempfile.TemporaryDirectory() as tmp:
        page_png = Path(png) if png else Path(tmp) / "page.png"
        img.save(page_png, dpi=(dpi, dpi))
        del img
        #without a layout the PDF page has exactly the size of the image at its dpi, nothing is scaled
        out_pdf.write_bytes(img2pdf.convert(str(page_png)))

    return {
        "pdf": out_pdf,
        "preview": preview,
        "size_px": (w, h),
        "size_mm": (round(w / dpi * 25.4, 2), round(h / dpi * 25.4, 2)),
        "codes": [(name, code) for name, code, _ in areas],
        "warnings": warnings,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description="Composes the printable page with OID codes as a PDF.")
    p.add_argument("svg", type=Path, help="the Inkscape drawing")
    p.add_argument("--objects", type=Path, required=True, help="objects.yaml written by svg_import")
    p.add_argument("--book-id", type=lambda s: int(s, 0), help="book number 701-9999, printed on @start")
    p.add_argument("--oid-map", type=Path, help="object -> code assignment (default oid_map.yaml next to objects.yaml)")
    p.add_argument("--dpi", type=int, default=1200, choices=oid.DPI_VALUES, help="printer resolution (default 1200)")
    p.add_argument("--lighten", type=float, default=LIGHTEN,
                   help=f"darkness kept by artwork under codes, 0-1 (default {LIGHTEN})")
    p.add_argument("--no-ruler", action="store_true", help="do not draw the 100 mm calibration ruler")
    p.add_argument("--png", type=Path, help="also save the full resolution page as PNG")
    p.add_argument("-o", "--output", type=Path, required=True, help="output PDF")
    a = p.parse_args(argv)
    try:
        r = compose(a.svg, a.objects, a.output, a.oid_map or a.objects.with_name("oid_map.yaml"), a.book_id,
                    a.dpi, a.lighten, not a.no_ruler, a.png)
    except (ComposeError, oid_map.OidMapError) as e:
        sys.exit(f"error: {e}")
    print(f"written {r['pdf']} ({r['size_px'][0]} x {r['size_px'][1]} px, {r['size_mm'][0]} x {r['size_mm'][1]} mm, "
          f"{a.dpi} dpi)")
    print(f"preview {r['preview']}")
    for name, code in r["codes"]:
        print(f"  {code:6}  {name}")
    for w in r["warnings"]:
        print(f"warning: {w}")


if __name__ == "__main__":
    main()
