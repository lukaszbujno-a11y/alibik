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
(also found in `~/perl5` via local::lib), otherwise those tests are skipped.

## Modules

- `albik.oid` - OID 2.0 code rendering, pixel-identical to `tools/oid_generator/oid_png_generator.pl`.
  `tile()` returns one tile, `fill()` covers an area with the grid anchored at the page origin.
  Also usable as a tool: `.venv/bin/python -m albik.oid 10000 --size 20 --dpi 1200 -o oid_10000.png`

## Data

`albik/data/oid_int2raw.bin` is the internal -> raw code table, generated from the Perl generator by
`python3 scripts/extract_oid_table.py`.
