"""Checks that albik.oid renders exactly the same codes as the reference Perl generator."""
import os
import subprocess
import shutil
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from albik import oid
from scripts.extract_oid_table import PERL_SOURCE, parse_perl_table

REPO = Path(__file__).resolve().parents[2]
PERL_GENERATOR = REPO / "tools" / "oid_generator" / "oid_png_generator.pl"


def perl_env():
    env = dict(os.environ)
    local_lib = Path.home() / "perl5" / "lib" / "perl5"
    if local_lib.is_dir():
        env["PERL5LIB"] = os.pathsep.join(filter(None, [str(local_lib), env.get("PERL5LIB")]))
    return env


def perl_has_imager():
    if not shutil.which("perl"):
        return False
    return subprocess.run(["perl", "-MImager", "-MYAML", "-e1"], env=perl_env(), capture_output=True).returncode == 0


needs_perl = pytest.mark.skipif(not perl_has_imager(), reason="perl with Imager and YAML is not available")


def test_table_matches_perl_source():
    table = parse_perl_table(PERL_SOURCE.read_text(encoding="utf-8-sig"))
    assert [oid.raw_code(i) for i in range(65536)] == table


def test_tile_size():
    #32 px at 600 dpi = 1.355 mm, the size the pen expects
    assert oid.tile(10000, 600).shape == (32, 32)
    assert oid.tile(10000, 1200).shape == (64, 64)
    assert oid.tile(10000, 600).sum() == 16  # 7 frame dots + 9 data dots


def test_fill_is_anchored_at_page_origin():
    page = oid.fill(10000, 300, 200, 1200)
    area = oid.fill(10000, 100, 50, 1200, origin=(37, 81))
    assert np.array_equal(area, page[81:131, 37:137])


@needs_perl
@pytest.mark.parametrize("code,dpi,size_x,size_y", [
    (10000, 1200, 20, 20),
    (10001, 1200, 18, 7.5),
    (8000, 600, 20, 20),
    (6, 600, 13.3, 9),
    (1, 1200, 5, 5),
    (65535, 600, 5, 5),
])
def test_matches_perl_generator(tmp_path, code, dpi, size_x, size_y):
    perl_png = tmp_path / "perl.png"
    subprocess.run(["perl", str(PERL_GENERATOR), str(code), "-sizex", str(size_x), "-sizey", str(size_y),
                    "-dpi", str(dpi), "-output", str(perl_png)], env=perl_env(), check=True, capture_output=True)
    expected = np.array(Image.open(perl_png).convert("RGBA"))[:, :, 3] > 0

    dots = oid.fill(code, oid.mm_to_px(size_x, dpi), oid.mm_to_px(size_y, dpi), dpi)
    assert np.array_equal(dots, expected)


def test_cli_writes_png_with_dpi(tmp_path):
    out = tmp_path / "x.png"
    oid.main(["10000", "--size", "10", "--dpi", "600", "-o", str(out)])
    img = Image.open(out)
    assert img.size == (236, 236)
    assert round(img.info["dpi"][0]) == 600
