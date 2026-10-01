"""Tests of albik.svg_import on a small drawing covering the naming conventions."""
import re
import shutil

import numpy as np
import pytest
import yaml
from PIL import Image

from albik import svg_import

needs_inkscape = pytest.mark.skipif(
    not (shutil.which("inkscape") or svg_import.Path("/Applications/Inkscape.app").exists()),
    reason="Inkscape is not installed")

#A4 in mm, 1 user unit = 1 mm
HEADER = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
          'width="210mm" height="297mm" viewBox="0 0 210 297">')

SCENE = HEADER + """
 <g inkscape:groupmode="layer" inkscape:label="Warstwa 1" id="layer1">
  <rect inkscape:label="_tlo" x="0" y="0" width="210" height="297" fill="#eef"/>
  <rect inkscape:label="krowa" id="krowa_shape" x="20" y="20" width="40" height="40" fill="#c96"/>
  <circle inkscape:label="kura" cx="70" cy="40" r="15" fill="#fc0"/>
  <g inkscape:label="Żółw">
   <circle cx="150" cy="60" r="20" fill="#6c6"/>
   <rect inkscape:label="ogon" x="168" y="58" width="15" height="4" fill="#6c6"/>
  </g>
  <rect inkscape:label="kot" x="20" y="100" width="20" height="20" fill="#999"/>
  <rect inkscape:label="kot" x="60" y="100" width="20" height="20" fill="#999"/>
  <rect inkscape:label="mysz" x="120" y="100" width="3" height="3" fill="#888"/>
  <rect inkscape:label="kruk" x="150" y="100" width="20" height="20" fill="black"/>
  <circle inkscape:label="@start" cx="30" cy="270" r="9" fill="#ddd"/>
 </g>
</svg>
"""

MM = svg_import.MASK_DPI / 25.4


def px(mm):
    return int(round(mm * MM))


@pytest.fixture(scope="module")
def imported(tmp_path_factory):
    d = tmp_path_factory.mktemp("scene")
    svg = d / "scene.svg"
    svg.write_text(SCENE, encoding="utf-8")
    result = svg_import.run(svg, d / "out")
    masks = {o["id"]: np.array(Image.open(d / "out" / o["mask"])) > 0 for o in result["objects"] + result["buttons"]}
    return d / "out", result, masks


def test_slugify():
    assert svg_import.slugify("Żółw morski") == "zolw_morski"
    assert svg_import.slugify("Łódź!") == "lodz"
    assert svg_import.slugify("krowa łaciata") == "krowa_laciata"


@needs_inkscape
def test_objects_and_buttons(imported):
    _, result, _ = imported
    assert [(o["id"], o["label"]) for o in result["objects"]] == [
        ("krowa", "krowa"), ("kura", "kura"), ("zolw", "Żółw"), ("kot", "kot"), ("mysz", "mysz"), ("kruk", "kruk")]
    assert [b["id"] for b in result["buttons"]] == ["start"]
    assert result["page"]["size_mm"] == [210.0, 297.0]


@needs_inkscape
def test_objects_yaml_is_written(imported):
    out, result, _ = imported
    assert yaml.safe_load((out / "objects.yaml").read_text(encoding="utf-8")) == result
    assert (out / "preview.png").exists()


@needs_inkscape
def test_same_label_is_one_object(imported):
    _, _, masks = imported
    kot = masks["kot"]
    assert kot[px(110), px(30)] and kot[px(110), px(70)]
    assert not kot[px(110), px(50)]


@needs_inkscape
def test_nested_label_is_part_of_object(imported):
    _, _, masks = imported
    assert "ogon" not in masks
    assert masks["zolw"][px(60), px(178)]


@needs_inkscape
def test_upper_object_wins_and_gap(imported):
    _, _, masks = imported
    krowa, kura = masks["krowa"], masks["kura"]
    #kura is drawn above krowa and covers its right edge
    assert kura[px(40), px(58)] and not krowa[px(40), px(58)]
    assert not (krowa & kura).any()
    #krowa keeps away from kura by about half of the 1 mm gap, kura by the other half
    assert krowa[px(40), px(53.5)]
    assert not krowa[px(40), px(54.8)]


@needs_inkscape
def test_artwork_is_not_an_object(imported):
    _, result, _ = imported
    assert "_tlo" not in {o["id"] for o in result["objects"]}


@needs_inkscape
def test_warnings(imported):
    _, result, _ = imported
    warnings = "\n".join(result["warnings"])
    assert "'mysz' is too small" in warnings
    assert re.search(r"'kruk' is \d+% dark", warnings)
    assert "Żółw" not in warnings
    assert "krowa" not in warnings
    assert "@start" not in warnings


@needs_inkscape
def test_missing_start_warns(tmp_path):
    svg = tmp_path / "s.svg"
    svg.write_text(HEADER + '<rect inkscape:label="krowa" x="20" y="20" width="40" height="40" fill="#c96"/></svg>')
    result = svg_import.run(svg, tmp_path / "out")
    assert any("no @start" in w for w in result["warnings"])


@pytest.mark.parametrize("body,message", [
    ('<rect inkscape:label="@play" x="0" y="0" width="9" height="9"/>', "unknown button '@play'"),
    ('<rect inkscape:label="Kot" x="0" y="0" width="9" height="9"/>'
     '<rect inkscape:label="kot" x="20" y="0" width="9" height="9"/>', "give the same id 'kot'"),
    ('<rect x="0" y="0" width="9" height="9"/>', "no labelled objects"),
])
def test_naming_errors(tmp_path, body, message):
    svg = tmp_path / "s.svg"
    svg.write_text(HEADER + body + "</svg>", encoding="utf-8")
    with pytest.raises(svg_import.SvgImportError, match=message):
        svg_import.run(svg, tmp_path / "out")
