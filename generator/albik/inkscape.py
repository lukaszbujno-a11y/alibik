"""Renders a drawing to PNG with Inkscape (found on PATH, in /Applications, or through the INKSCAPE variable)."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image

MAC_APP = "/Applications/Inkscape.app/Contents/MacOS/inkscape"


class InkscapeError(Exception):
    pass


def binary() -> str:
    exe = os.environ.get("INKSCAPE") or shutil.which("inkscape")
    if not exe and Path(MAC_APP).exists():
        exe = MAC_APP
    if not exe:
        raise InkscapeError("Inkscape not found; install it or set INKSCAPE to its binary")
    return exe


def render_png(svg: Path, out: Path, dpi: int, background: str = None, antialias: bool = True) -> Image.Image:
    """Renders the whole page; without a background the page is transparent.

    With antialias off every pixel has exactly the colour of the shape covering it.
    """
    actions = ["export-type:png", f"export-dpi:{dpi}", "export-area-page"]
    if background:
        actions += [f"export-background:{background}", "export-background-opacity:1", "export-png-color-mode:RGB_8"]
    else:
        actions += ["export-background-opacity:0"]
    if not antialias:
        actions += ["export-png-antialias:0"]
    actions += [f"export-filename:{out}", "export-do"]
    r = subprocess.run([binary(), str(svg), "--actions=" + ";".join(actions)], capture_output=True, text=True)
    if r.returncode != 0 or not out.exists():
        raise InkscapeError("Inkscape export failed:\n" + r.stderr)
    img = Image.open(out)
    img.load()  # read now, the file may be in a temporary directory
    return img
