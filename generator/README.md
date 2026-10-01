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

## Usage: from a drawing to a printable page

All commands are run from the `generator` directory. Sounds and the `.bnl` file are not generated yet.

### 1. Draw the page in Inkscape

- Document size **A4 in millimeters**.
- Every object the pen should react to is a group, a shape or an image with a **name** - set it in the
  Layers and Objects panel (Ctrl+Shift+L / ⌘+Shift+L, double-click the name). The name is what the pen says,
  e.g. `kot`, `krowa łaciata`.
- Several elements with the same name form one object.
- A name starting with `_` (e.g. `_tytul`) is artwork without a code.
- Pen buttons are named `@start` (required, activates the book), `@volume_up`, `@volume_down`, `@stop`,
  `@compare`, `@mode_1` ... `@mode_12`.
- Keep coded objects light and at least ~5 mm wide; dark areas hide the code.
- Save the file (⌘S) before running the tools.

### 2. Find the objects

```sh
.venv/bin/python -m albik.svg_import ~/Pictures/drawing.svg -o ~/Pictures/drawing_build
open ~/Pictures/drawing_build/preview.png
```

Prints the objects and warnings:

```
2 objects, 1 buttons -> /Users/.../drawing_build/objects.yaml
   1 kot
   2 lis
   3 @start
warning: 'lis' is 20% dark - dark areas may hide the code
```

Check `preview.png`: every object is tinted and numbered; the code will cover exactly the tinted areas.
Fix the drawing and run the command again until the list and the preview are right.

### 3. Compose the printable page

```sh
.venv/bin/python -m albik.page_composer ~/Pictures/drawing.svg \
    --objects ~/Pictures/drawing_build/objects.yaml --book-id 8000 \
    -o ~/Pictures/drawing_build/page.pdf
open ~/Pictures/drawing_build/page.pdf
```

Prints the codes given to the objects:

```
written .../page.pdf (9921 x 14031 px, 209.99 x 296.99 mm, 1200 dpi)
   10000  kot
   10001  lis
    8000  @start
```

- `--book-id` is the book number 701-9999 printed on `@start`; it must be unique among the books on the pen.
- The codes are kept in `oid_map.yaml` next to `objects.yaml`. **Keep this file** - the same objects then
  get the same codes on every run, so already printed pages stay valid.

### 4. Print and check

- Print the PDF at **actual size / 100 %**, highest quality; see the printing tips in
  [docs/creating_a_book.md](../docs/creating_a_book.md#printing-tips).
- Measure the ruler at the bottom of the page - it must be exactly 100 mm.
- Check the codes in the pen **test mode** (pen 2.0): switch the pen on while holding the power and Vol+
  buttons; it then speaks every code it reads as a number (in Chinese).

### Options

| Tool | Option | Default | Meaning |
|---|---|---|---|
| `svg_import` | `--gap MM` | 1 | gap between touching objects |
| `svg_import` | `--min-size MM` | 5 | warn about objects narrower than this |
| `svg_import` | `--mask-dpi N` | 300 | mask resolution |
| `page_composer` | `--dpi 600\|1200` | 1200 | printer resolution - use the native one of your printer |
| `page_composer` | `--lighten F` | 0.4 | darkness kept by the artwork under codes (0 = white, 1 = unchanged) |
| `page_composer` | `--oid-map FILE` | next to `objects.yaml` | object -> code assignment |
| `page_composer` | `--no-ruler` | | no 100 mm calibration ruler |
| `page_composer` | `--png FILE` | | also save the full resolution page as PNG |

All options: `.venv/bin/python -m albik.svg_import --help`, `.venv/bin/python -m albik.page_composer --help`.

### Error messages

| Message | Fix |
|---|---|
| `no labelled objects found` | name the objects in Inkscape and save the file |
| `unknown button '@...'` | use one of the listed button names |
| `labels 'Kot' and 'kot' give the same id` | rename one of the objects |
| `the drawing has a @start button, the book id is needed` | add `--book-id` |
| `'...' is too small or thin for the pen` (warning) | make the object larger |
| `'...' is N% dark` (warning) | use lighter colors, or check that area on a test print |
| `no @start button` (warning) | add a `@start` button, otherwise the book cannot be activated |
| `Inkscape not found` | install Inkscape or set `INKSCAPE` to its binary |

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
