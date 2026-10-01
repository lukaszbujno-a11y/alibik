"""Finds the objects of an Inkscape drawing and exports their masks.

Conventions (docs/drawing_to_book/README.md):
- every element with an Inkscape label (a renamed group or shape) is an object with an OID code,
  the label is the text the pen says,
- a label starting with "_" is artwork without a code,
- a label starting with "@" is a pen button (@start, @volume_up, @volume_down, @stop, @compare, @mode_N),
- several elements with the same label form one object,
- layers are only containers, labelled elements inside another labelled element are part of it.

Output in the output directory:
- objects.yaml - the list of objects and buttons with their masks,
- masks/*.png - 1-bit masks of the whole page at mask_dpi (white = object),
- preview.png - the page with numbered object outlines for review.

Usage:
    python -m albik.svg_import scene.svg -o build/
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

from albik.oid_map import BUTTON_CODES

SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
LABEL = f"{{{INKSCAPE_NS}}}label"
GROUPMODE = f"{{{INKSCAPE_NS}}}groupmode"
NAMESPACES = {
    "": SVG_NS,
    "inkscape": INKSCAPE_NS,
    "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
    "xlink": "http://www.w3.org/1999/xlink",
}

BUTTONS = {"start"} | set(BUTTON_CODES)
UNITS_MM = {"mm": 1.0, "cm": 10.0, "in": 25.4, "pt": 25.4 / 72, "pc": 25.4 / 6, "px": 25.4 / 96, "": 25.4 / 96}
A4_MM = (210.0, 297.0)

#defaults, all in mm
MASK_DPI = 300
GAP_MM = 1.0
MIN_SIZE_MM = 5.0
#a pixel of the artwork is dark below this luminance; warn when more than DARK_SHARE of an object is dark
DARK_LUMINANCE = 80
DARK_SHARE = 0.2
#fonts with Polish letters for the preview, the first one found is used
PREVIEW_FONTS = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
)


@dataclass
class PageObject:
    label: str
    id: str
    button: bool
    elements: list = field(default_factory=list)  # svg ids in document order
    mask: np.ndarray = None


class SvgImportError(Exception):
    pass


def slugify(label: str) -> str:
    """'Żółw morski' -> 'zolw_morski'; letters without a decomposition (ł) are mapped by hand."""
    text = label.replace("ł", "l").replace("Ł", "L")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def parse_length_mm(value: str) -> float:
    m = re.fullmatch(r"\s*([0-9.]+)\s*([a-z]*)\s*", value or "")
    if not m or m.group(2) not in UNITS_MM:
        raise SvgImportError(f"unsupported page size '{value}'")
    return float(m.group(1)) * UNITS_MM[m.group(2)]


def page_size_mm(root: ET.Element) -> tuple:
    if root.get("width") and root.get("height"):
        return parse_length_mm(root.get("width")), parse_length_mm(root.get("height"))
    vb = (root.get("viewBox") or "").replace(",", " ").split()
    if len(vb) == 4:
        return float(vb[2]) * UNITS_MM["px"], float(vb[3]) * UNITS_MM["px"]
    raise SvgImportError("the drawing has no page size")


def find_objects(root: ET.Element) -> list:
    """Collects labelled elements in document order (= bottom to top) and groups them by label."""
    objects = {}
    used_ids = {el.get("id") for el in root.iter() if el.get("id")}
    counter = 0

    def visit(el):
        nonlocal counter
        for child in el:
            label = (child.get(LABEL) or "").strip()
            is_layer = child.get(GROUPMODE) == "layer"
            if not label or is_layer:
                visit(child)
                continue
            if label.startswith("_"):
                continue
            button = label.startswith("@")
            oid = label[1:] if button else slugify(label)
            if button and oid not in BUTTONS:
                raise SvgImportError(f"unknown button '{label}', known: " + ", ".join("@" + b for b in sorted(BUTTONS)))
            if not oid:
                raise SvgImportError(f"label '{label}' gives an empty id")
            key = ("@" if button else "") + oid
            obj = objects.get(key)
            if obj is None:
                obj = objects[key] = PageObject(label=label, id=oid, button=button)
            elif obj.label != label:
                raise SvgImportError(f"labels '{obj.label}' and '{label}' give the same id '{oid}', rename one of them")
            if not child.get("id"):
                while f"albik_{counter}" in used_ids:
                    counter += 1
                child.set("id", f"albik_{counter}")
                used_ids.add(child.get("id"))
            obj.elements.append(child.get("id"))
            #labelled elements inside an object are part of it, not separate objects

    visit(root)
    return list(objects.values())


def inkscape_binary() -> str:
    exe = os.environ.get("INKSCAPE") or shutil.which("inkscape")
    if not exe and Path("/Applications/Inkscape.app/Contents/MacOS/inkscape").exists():
        exe = "/Applications/Inkscape.app/Contents/MacOS/inkscape"
    if not exe:
        raise SvgImportError("Inkscape not found; install it or set INKSCAPE to its binary")
    return exe


def export_pngs(svg: Path, element_ids: list, out_dir: Path, dpi: int) -> tuple:
    """Exports every element alone on the whole page, plus the whole page on white; one Inkscape run."""
    actions = ["export-type:png", f"export-dpi:{dpi}", "export-area-page"]
    actions += ["export-background:white", "export-background-opacity:1",
                f"export-filename:{out_dir / 'page.png'}", "export-do"]
    actions += ["export-background-opacity:0", "export-id-only"]
    files = []
    for i, eid in enumerate(element_ids):
        f = out_dir / f"el_{i}.png"
        actions += [f"export-id:{eid}", f"export-filename:{f}", "export-do"]
        files.append(f)
    r = subprocess.run([inkscape_binary(), str(svg), "--actions=" + ";".join(actions)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SvgImportError("Inkscape export failed:\n" + r.stderr)
    return out_dir / "page.png", files


def compute_masks(objects: list, element_masks: dict, gap_px: float) -> None:
    """Element masks minus everything of other objects above them, then a gap between neighbouring objects."""
    shape = next(iter(element_masks.values())).shape
    for obj in objects:
        obj.mask = np.zeros(shape, dtype=bool)

    #element_masks is in document order = z-order; walk from the top, everything above covers what is below
    sequence = list(element_masks)
    owner = {eid: obj for obj in objects for eid in obj.elements}
    covered = np.zeros(shape, dtype=bool)
    for eid in reversed(sequence):
        visible = element_masks[eid] & ~covered
        owner[eid].mask |= visible
        covered |= element_masks[eid]

    if gap_px <= 0:
        return
    half = gap_px / 2
    originals = [o.mask.copy() for o in objects]
    for i, obj in enumerate(objects):
        others = np.zeros(shape, dtype=bool)
        for j, m in enumerate(originals):
            if j != i:
                others |= m
        if not others.any() or not obj.mask.any():
            continue
        ys, xs = np.nonzero(obj.mask)
        pad = int(np.ceil(half)) + 1
        y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, shape[0])
        x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, shape[1])
        window = others[y0:y1, x0:x1]
        if not window.any():
            continue
        near = ndimage.distance_transform_edt(~window) <= half
        obj.mask[y0:y1, x0:x1] &= ~near


def element_order(root: ET.Element, objects: list) -> list:
    wanted = {eid for obj in objects for eid in obj.elements}
    return [el.get("id") for el in root.iter() if el.get("id") in wanted]


def run(svg_path: Path, out_dir: Path, mask_dpi: int = MASK_DPI, gap_mm: float = GAP_MM,
        min_size_mm: float = MIN_SIZE_MM) -> dict:
    for prefix, uri in NAMESPACES.items():
        ET.register_namespace(prefix, uri)
    tree = ET.parse(svg_path)
    root = tree.getroot()
    page_mm = page_size_mm(root)
    objects = find_objects(root)
    warnings = []
    if not objects:
        raise SvgImportError("no labelled objects found; name the groups in Inkscape (Layers and Objects panel)")
    if any(abs(a - b) > 0.5 for a, b in zip(page_mm, A4_MM)):
        warnings.append(f"page is {page_mm[0]:.1f} x {page_mm[1]:.1f} mm, not A4")
    if not any(o.button and o.id == "start" for o in objects):
        warnings.append("no @start button - the book cannot be activated without its start icon")

    out_dir.mkdir(parents=True, exist_ok=True)
    masks_dir = out_dir / "masks"
    if masks_dir.exists():
        shutil.rmtree(masks_dir)
    masks_dir.mkdir()

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        #work on a copy with ids added to labelled elements that had none
        svg_copy = tmp / "scene.svg"
        tree.write(svg_copy, encoding="utf-8", xml_declaration=True)
        ids = element_order(root, objects)
        page_png, files = export_pngs(svg_copy, ids, tmp, mask_dpi)
        page_rgb = np.array(Image.open(page_png).convert("RGB"))
        element_masks = {eid: np.array(Image.open(f).convert("RGBA"))[:, :, 3] > 127 for eid, f in zip(ids, files)}

    px_per_mm = mask_dpi / 25.4
    compute_masks(objects, element_masks, gap_mm * px_per_mm)

    rgb = page_rgb.astype(np.float32)
    luminance = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    result_objects, result_buttons = [], []
    for obj in objects:
        name = f"{'button_' if obj.button else ''}{obj.id}.png"
        Image.fromarray(obj.mask).save(masks_dir / name, dpi=(mask_dpi, mask_dpi))
        shown = "@" + obj.id if obj.button else obj.label
        entry = {"id": obj.id, "mask": f"masks/{name}"} if obj.button else \
            {"id": obj.id, "label": obj.label, "mask": f"masks/{name}"}
        if not obj.mask.any():
            warnings.append(f"'{shown}' is empty (hidden, fully covered by other objects, or not drawn)")
            entry["bbox_mm"] = None
        else:
            ys, xs = np.nonzero(obj.mask)
            entry["bbox_mm"] = [round(float(v) / px_per_mm, 1) for v in
                                (xs.min(), ys.min(), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1)]
            entry["area_mm2"] = round(float(obj.mask.sum()) / px_per_mm ** 2, 1)
            inscribed = 2 * ndimage.distance_transform_edt(np.pad(obj.mask, 1)).max() / px_per_mm
            if inscribed < min_size_mm:
                warnings.append(f"'{shown}' is too small or thin for the pen: widest part {inscribed:.1f} mm, "
                                f"at least {min_size_mm:g} mm recommended")
            dark = float((luminance[obj.mask] < DARK_LUMINANCE).mean())
            if dark > DARK_SHARE:
                warnings.append(f"'{shown}' is {dark:.0%} dark - dark areas may hide the code")
        (result_buttons if obj.button else result_objects).append(entry)

    mask_size = [int(page_rgb.shape[1]), int(page_rgb.shape[0])]
    result = {
        "source": svg_path.name,
        "page": {"size_mm": [round(page_mm[0], 2), round(page_mm[1], 2)], "mask_dpi": mask_dpi,
                 "mask_size_px": mask_size, "gap_mm": gap_mm},
        "objects": result_objects,
        "buttons": result_buttons,
        "warnings": warnings,
    }
    with open(out_dir / "objects.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(result, f, allow_unicode=True, sort_keys=False)
    write_preview(out_dir / "preview.png", page_rgb, objects)
    return result


def write_preview(path: Path, page_rgb: np.ndarray, objects: list) -> None:
    """Lightened page, every object tinted and outlined, numbered in the order of objects.yaml."""
    img = (255 - (255 - page_rgb.astype(np.float32)) * 0.35).astype(np.uint8)
    rng = np.random.default_rng(1)
    numbered = [o for o in objects if not o.button] + [o for o in objects if o.button]
    for obj in numbered:
        color = rng.integers(40, 220, 3)
        img[obj.mask] = (img[obj.mask] * 0.55 + color * 0.45).astype(np.uint8)
        edge = obj.mask & ~ndimage.binary_erosion(obj.mask, iterations=3)
        img[edge] = color
    out = Image.fromarray(img)
    draw = ImageDraw.Draw(out)
    size = max(out.width // 60, 12)
    font_file = next((f for f in PREVIEW_FONTS if Path(f).exists()), None)
    font = ImageFont.truetype(font_file, size) if font_file else ImageFont.load_default()
    for n, obj in enumerate(numbered, 1):
        if not obj.mask.any():
            continue
        #put the number at the point deepest inside the object
        dist = ndimage.distance_transform_edt(obj.mask)
        y, x = np.unravel_index(np.argmax(dist), dist.shape)
        text = f"{n} {'@' + obj.id if obj.button else obj.label}"
        draw.text((int(x), int(y)), text, fill="black", font=font, anchor="mm", stroke_width=max(size // 8, 2),
                  stroke_fill="white")
    out.save(path)


def main(argv=None):
    p = argparse.ArgumentParser(description="Finds labelled objects in an Inkscape drawing and exports their masks.")
    p.add_argument("svg", type=Path)
    p.add_argument("-o", "--output", type=Path, required=True, help="output directory")
    p.add_argument("--mask-dpi", type=int, default=MASK_DPI, help=f"mask resolution (default {MASK_DPI})")
    p.add_argument("--gap", type=float, default=GAP_MM, help=f"gap between touching objects in mm (default {GAP_MM:g})")
    p.add_argument("--min-size", type=float, default=MIN_SIZE_MM,
                   help=f"warn about objects narrower than this in mm (default {MIN_SIZE_MM:g})")
    a = p.parse_args(argv)
    try:
        result = run(a.svg, a.output, a.mask_dpi, a.gap, a.min_size)
    except SvgImportError as e:
        sys.exit(f"error: {e}")
    print(f"{len(result['objects'])} objects, {len(result['buttons'])} buttons -> {a.output / 'objects.yaml'}")
    for n, o in enumerate(result["objects"] + result["buttons"], 1):
        print(f"  {n:2} {o.get('label', '@' + o['id'])}")
    for w in result["warnings"]:
        print(f"warning: {w}")


if __name__ == "__main__":
    main()
