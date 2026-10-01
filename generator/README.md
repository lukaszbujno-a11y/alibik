# albik - book generator (Python)

Tools for the pipeline described in [docs/drawing_to_book/README.md](../docs/drawing_to_book/README.md).
Work in progress; the original Perl tools in [tools/](../tools/) stay unchanged, `bnl_creator.pl` is used as is.

## Setup

```sh
cd generator
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python -m pytest
```

The tests compare the output with the Perl generator; they need Perl with `Imager` and `YAML`
(also found in `~/perl5` via local::lib), otherwise those tests are skipped. The `svg_import` tests need
Inkscape and are skipped without it.

Inkscape (free) is needed for the drawing tools: `brew install --cask inkscape` on macOS, or
https://inkscape.org. It is found on PATH, in `/Applications`, or through the `INKSCAPE` variable.

## Modules

- `albik.oid` - OID 2.0 code rendering, pixel-identical to `tools/oid_generator/oid_png_generator.pl`.
  `tile()` returns one tile, `fill()` covers an area with the grid anchored at the page origin.
  Also usable as a tool: `.venv/bin/python -m albik.oid 10000 --size 20 --dpi 1200 -o oid_10000.png`
- `albik.svg_import` - finds the labelled objects of an Inkscape drawing and exports their masks:
  `.venv/bin/python -m albik.svg_import scene.svg -o build/` writes `build/objects.yaml`, `build/masks/*.png`
  (whole page at 300 dpi, white = object) and `build/preview.png` with numbered objects for review.
  Upper objects cover lower ones, touching objects get a 1 mm gap (`--gap`); warns about objects that are
  too small (`--min-size`) or too dark. Needs Inkscape (found on PATH, in `/Applications`, or via `INKSCAPE`).
- `albik.oid_map` - stable object -> code assignment kept in `oid_map.yaml` (codes 10000-49999, a removed
  object keeps its code) and the codes of the pen buttons.
- `albik.page_composer` - the printable page:
  `.venv/bin/python -m albik.page_composer scene.svg --objects build/objects.yaml --book-id 8000 -o build/page.pdf`
  renders the drawing at the printer resolution (`--dpi 600|1200`), lightens it under the codes (`--lighten`),
  fills every object mask with its code on a grid anchored at the page origin, draws a 100 mm calibration
  ruler (`--no-ruler`) and writes one lossless raster 1:1 into the PDF; also `build/page_preview.png`.
  Codes are assigned in `oid_map.yaml` next to `objects.yaml` unless `--oid-map` is given.
  At 1200 dpi an A4 page takes about 8 s and up to 2.5 GB of memory.

## Data

`albik/data/oid_int2raw.bin` is the internal -> raw code table, generated from the Perl generator by
`python3 scripts/extract_oid_table.py`.
