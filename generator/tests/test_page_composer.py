"""Tests of albik.oid_map and albik.page_composer."""
import re

import numpy as np
import pytest
import yaml
from PIL import Image

from albik import oid, oid_map, page_composer, svg_import
from tests.test_svg_import import HEADER, needs_inkscape

Image.MAX_IMAGE_PIXELS = None

SCENE = HEADER + """
 <rect inkscape:label="_tlo" x="0" y="0" width="210" height="297" fill="#ddeeff"/>
 <rect inkscape:label="krowa" x="20" y="20" width="40" height="40" fill="#c96"/>
 <circle inkscape:label="kura" cx="120" cy="40" r="15" fill="#fc0"/>
 <circle inkscape:label="@start" cx="30" cy="250" r="9" fill="#ddd"/>
 <rect inkscape:label="@volume_up" x="60" y="241" width="18" height="18" fill="#ddd"/>
</svg>
"""


def test_assign_is_stable(tmp_path):
    path = tmp_path / "oid_map.yaml"
    assert oid_map.assign(path, ["krowa", "kura"]) == {"krowa": 10000, "kura": 10001}
    #kura stays, krowa disappears from the drawing but keeps its code, kot gets the next one
    assert oid_map.assign(path, ["kura", "kot"]) == {"kura": 10001, "kot": 10002}
    assert oid_map.load(path) == {"krowa": 10000, "kura": 10001, "kot": 10002}


def test_hand_edited_map_is_checked(tmp_path):
    path = tmp_path / "oid_map.yaml"
    path.write_text("krowa: 500\n")
    with pytest.raises(oid_map.OidMapError, match="must be a number 10000-49999"):
        oid_map.load(path)
    path.write_text("krowa: 10000\nkura: 10000\n")
    with pytest.raises(oid_map.OidMapError, match="used twice"):
        oid_map.load(path)


def test_button_codes():
    assert oid_map.button_code("start", 8000) == 8000
    assert oid_map.button_code("volume_up") == 7
    with pytest.raises(oid_map.OidMapError, match="book id is needed"):
        oid_map.button_code("start")
    with pytest.raises(oid_map.OidMapError, match="out of range"):
        oid_map.button_code("start", 10000)


@pytest.fixture(scope="module")
def composed(tmp_path_factory):
    d = tmp_path_factory.mktemp("compose")
    svg = d / "scene.svg"
    svg.write_text(SCENE, encoding="utf-8")
    svg_import.run(svg, d / "build")
    png = d / "page.png"
    result = page_composer.compose(svg, d / "build" / "objects.yaml", d / "page.pdf", d / "oid_map.yaml",
                                   book_id=8000, dpi=600, png=png)
    page = np.array(Image.open(png).convert("RGB"))
    objects = yaml.safe_load((d / "build" / "objects.yaml").read_text(encoding="utf-8"))
    masks = {o["id"]: np.array(Image.open(d / "build" / o["mask"])) > 0 for o in objects["objects"] + objects["buttons"]}
    return d, result, page, masks


def full_res(mask, shape, mask_dpi=svg_import.MASK_DPI, dpi=600):
    ys = np.minimum(np.arange(shape[0]) * mask_dpi // dpi, mask.shape[0] - 1)
    xs = np.minimum(np.arange(shape[1]) * mask_dpi // dpi, mask.shape[1] - 1)
    return mask[np.ix_(ys, xs)]


@needs_inkscape
def test_pdf_page_is_a4_and_lossless(composed):
    d, result, _, _ = composed
    pdf = (d / "page.pdf").read_bytes()
    box = [float(v) for v in re.search(rb"/MediaBox \[ ([\d. ]+) \]", pdf).group(1).split()]
    assert abs(box[2] / 72 * 25.4 - 210) < 0.1 and abs(box[3] / 72 * 25.4 - 297) < 0.1
    assert b"/FlateDecode" in pdf and b"/DCTDecode" not in pdf
    assert b"/Interpolate true" not in pdf
    assert result["preview"].exists()


@needs_inkscape
def test_codes(composed):
    _, result, _, _ = composed
    assert result["codes"] == [("krowa", 10000), ("kura", 10001), ("@start", 8000), ("@volume_up", 7)]


@needs_inkscape
@pytest.mark.parametrize("name,code", [("krowa", 10000), ("kura", 10001), ("start", 8000), ("volume_up", 7)])
def test_dots_are_the_code_on_the_page_grid(composed, name, code):
    _, _, page, masks = composed
    h, w = page.shape[:2]
    inside = full_res(masks[name], (h, w))
    dots = np.all(page == 0, axis=2)
    expected = oid.fill(code, w, h, 600)
    assert np.array_equal(dots[inside], expected[inside])


@needs_inkscape
def test_artwork_is_lightened_only_under_codes(composed):
    _, _, page, masks = composed
    px = 600 / 25.4
    #background #ddeeff stays as drawn outside objects
    assert tuple(page[int(150 * px), int(150 * px)]) == (0xdd, 0xee, 0xff)
    #krowa #cc9966 keeps 40 % of its darkness, except the dots
    y, x = int(40 * px), int(40 * px)
    window = page[y:y + 40, x:x + 40].reshape(-1, 3)
    art = window[~np.all(window == 0, axis=1)][0]
    lut = lambda v: int(255 - (255 - v) * 0.4 + 0.5)
    assert tuple(art) == (lut(0xcc), lut(0x99), lut(0x66))


@needs_inkscape
def test_no_dots_outside_objects_except_ruler(composed):
    _, _, page, masks = composed
    h, w = page.shape[:2]
    coded = np.zeros((h, w), dtype=bool)
    for m in masks.values():
        coded |= full_res(m, (h, w))
    black = np.all(page == 0, axis=2) & ~coded
    ruler_top = h - int(16 * 600 / 25.4)
    assert not black[:ruler_top].any()
    assert black[ruler_top:].any()


@needs_inkscape
def test_start_needs_book_id(tmp_path):
    svg = tmp_path / "scene.svg"
    svg.write_text(SCENE, encoding="utf-8")
    svg_import.run(svg, tmp_path / "build")
    with pytest.raises(oid_map.OidMapError, match="book id is needed"):
        page_composer.compose(svg, tmp_path / "build" / "objects.yaml", tmp_path / "p.pdf", tmp_path / "m.yaml", dpi=600)
