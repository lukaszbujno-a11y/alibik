# From a drawing to a book - concept

Status: **concept agreed, not implemented yet.**

The goal is a mostly automatic pipeline: you draw a page with many objects in Inkscape, name the objects,
and the tools produce the `.bnl` file for the pen and a printable PDF with the OID codes laid over the
drawing. The manual workflow in [creating_a_book.md](../creating_a_book.md) stays valid; this pipeline
builds on the same tools (`bnl_creator.pl`, the OID tile from `oid_png_generator.pl`).

All tools used by default are **free**.

## The problem it solves: OID codes must never be scaled

The pen reads a code only at its exact physical size. One OID2 tile is 32 px at 600 dpi (≈1.355 mm),
one dot is 1 px at 600 dpi. If the code is scaled, the pen does not read it. Today the code size can break
in four places:

1. an `oid_*.png` is placed into a graphics program and resized to fit the picture,
2. the composed page is exported or resized at a different dpi,
3. the page is printed with "fit to page" or the printer margins shrink it by a few percent,
4. the printer driver resamples the page because its native resolution differs (600 vs 1200 dpi).

**Rule of the pipeline: the drawing may be scaled freely, the OID codes never.** Codes are not images that
get placed - they are a "paint" applied in the last step to object shapes described in millimetres, rendered
directly at the printer resolution, and nothing scales the page afterwards.

## Pipeline

```
scene.svg (Inkscape) --svg_import--> objects.yaml + masks/*.png
                                         |
                                     [review]
                                         |
            book.yaml + objects.yaml --book_gen--> bnl.yaml + content/ (texts, mp3) --bnl_creator.pl--> book.bnl
                                         |
            scene.svg + masks + OIDs --page_composer--> page.pdf (A4, 1 raster at printer dpi)
                                         |
                                     oid_check (verifies the dot period on the composed page)
```

Planned tools (Perl, like the rest of the repository), in `tools/`:

| Tool | Input | Output |
|---|---|---|
| `svg_import` | Inkscape SVG | `objects.yaml`, one mask PNG per object, warnings |
| `book_gen` | `book.yaml`, `objects.yaml` | `bnl.yaml`, sounds in `content/` |
| `page_composer` | SVG, masks, OID assignment | `page.pdf` |
| `oid_check` | composed page | pass/fail of the OID dot period per area |

## Step 1: Drawing in Inkscape

Conventions - the only "marking" you do is naming groups in the Layers and Objects panel:

- The document is **A4 in millimetres**.
- **A named group is an object with an OID code.** Draw a cow from several shapes, group them (Ctrl+G) and
  name the group `krowa`.
- **The group name is the text the pen says.** `krowa` -> "krowa", `krowa łaciata` -> "krowa łaciata".
- **A name starting with `_`** (e.g. `_tlo`, `_tytul`) is artwork only, without a code.
- **A name starting with `@`** is a pen button: `@start` (prints the `book_id`), `@volume_up`,
  `@volume_down`, `@stop`, later `@mode_2`, ... for categories.
- **The same name on several groups means the same code** - two cows both say "krowa".
- File names and keys are derived automatically without diacritics: `żółw` -> `zolw.mp3`, `oid_10003_zolw`.

Drawing style recommendations, because the pen sees the dots in infrared:

- flat, light colors under coded objects; large dark areas make codes unreadable,
- objects at least ~5×5 mm (several tiles),
- a small gap between neighbouring objects,
- the reader sees practically only carbon-based black (black toner, pigment black ink); color inks/toners are
  mostly invisible to it. So dark areas of the artwork should be mixed from colors (CMY), not printed with
  black, otherwise they cover the dots. Whether the printer driver keeps it that way is checked with the
  test sheet (see [Verification](#step-6-verification)). This comes from general OID experience, not from
  the Albi documents.

## Step 2: Object detection (`svg_import`)

- Reads the SVG and lists the named groups.
- Exports a mask of every group through the Inkscape command line, positioned on the whole page and at the
  target dpi, e.g.:
  `inkscape scene.svg --export-id=krowa --export-id-only --export-area-page --export-dpi=1200 -o masks/krowa.png`
- Shrinks every mask by ~1 mm, so the pen never reads a mixture of two codes where objects touch.
  Overlaps are resolved by the order of the groups (the upper group wins).
- Warns about objects that are too small and areas that are too dark under the code.
- Produces a preview with numbered outlines for review before anything is built.

Detection from named groups is exact and needs no AI. Other detectors (connected components on a flat
image, AI segmentation for ready-made pictures) can be added later as long as they produce the same
`objects.yaml`.

## Step 3: Object list (`objects.yaml`)

The common format between detection and generation:

```yaml
page: { size: A4, dpi: 1200 }
objects:
  - id: krowa             # derived key, no diacritics
    label: krowa          # spoken text (the group name)
    mask: masks/krowa.png
    bbox_mm: [22, 30, 160, 105]
  - id: kura
    label: kura
    mask: masks/kura.png
buttons:
  - id: "@start"
    mask: masks/at_start.png
```

**OID codes are assigned stably.** Object codes start at 10000 like official books. The assignment
(id -> code) is stored in the book directory and reused on every run, so adding a new object never changes
the codes of already printed objects. One book can have several SVG pages; the same name on different
pages gets the same code.

**Code ranges** (from [the BNL format](../en/albituzka_bnl_format.md#default-values)) that the generator must
respect:

| Range | Used for |
|---|---|
| 701–9999 | `book_id` (printed on the start icon) |
| 100–499 | quizzes |
| **10000–49999** | **objects of our books (safe range used by the generator)** |
| ~52000 and up (0xCB3A–) | recording, calculator and other firmware functions |
| 54001–57674 (0xD2F1–0xE14A) | the firmware starts playing `.tn2` files |
| ~60000 and up (0xEA61–) | WAV recording/playback |

Codes outside the safe range are rejected.

## Step 4: Content generation (`book_gen`)

### Categories are book modes

The BNL format has up to 12 modes, each with its own printable mode icon, and every code can play a different
sound in each mode. Content categories map to modes:

Official books use fixed icons for the modes, so categories follow their meaning - a child who knows the
official books recognizes the symbols:

| Category | Mode | Official icon | When |
|---|---|---|---|
| **Recognition** ("krowa") | `mode_0` + `mode_1` | open book | **stage 1** |
| Facts | `mode_2` | light bulb | later |
| Sounds | `mode_4` | note | later |
| Quiz | the `quizes` section of BNL | dice | later |

Rules from the [BNL format](../en/albituzka_bnl_format.md):

- **Modes 0 and 1 alternate.** In mode 0 the pen plays the sound of mode 0 and mode 1 in turn when the same
  object is tapped again. Official books have both identical, so `book_gen` **always copies `mode_0` into
  `mode_1`**; otherwise every second tap could stay silent.
- **An object that should stay silent in a mode needs an empty sound**, not a missing entry.
- **Several sounds in one entry are played one after another.** A later category can combine e.g. "krowa"
  followed by a moo in a single tap.

### Replaceable providers

Every content source is a provider behind a common interface, switched by one line in `book.yaml`:

```yaml
book_id: 0x1F40
title: Na wsi
pages: [scene.svg]
print: { dpi: 1200 }

content:
  voice: { provider: say, voice: Zosia }                          # say | piper
  text:  { provider: wikipedia, lang: pl, max_sentences: 3 }      # wikipedia | wikipedia+llm | manual  (later)
  sfx:   { provider: freesound, license: cc0, max_seconds: 5 }    # freesound | local | none          (later)
```

| Element | Start | Free alternative later |
|---|---|---|
| Voice | macOS `say`, voice Zosia | Piper (offline, Polish voices) |
| Facts | Wikipedia (REST summary API) | Wikipedia facts simplified for children by a local LLM (Ollama) |
| Animal sounds | Freesound, CC0 only (free API key) | local directory with recordings |

Wikipedia alone writes in encyclopedic language; a pure LLM may invent facts. The intended combination is
facts from Wikipedia rewritten into simple sentences by an LLM. Paid services (e.g. a hosted LLM API) are
never a default, at most an optional provider.

Rules common to all providers:

- **Results are stored as editable files** (`content/<id>.yaml`, mp3). The generator only fills in what is
  missing; manual edits are never overwritten, and an object can be marked `locked: true`.
- **Safe for children:** all recordings are normalized to one loudness with a peak limit (ffmpeg `loudnorm`),
  silence is trimmed, sound effects are cut to a few seconds.
- **Review before build:** a listing of all texts and sounds to read and listen to before the `.bnl` is built.

## Step 5: Page composition (`page_composer`)

- Renders the SVG artwork through Inkscape at the target dpi.
- Lightens the artwork under coded objects (as `LIGHTEN` in `test/my-book/make_page.pl`).
- Fills every mask with the OID tile of its code. The tile is generated once per code directly at the
  target dpi (logic of `create_OID_tile` in `oid_png_generator.pl`) and the grid is anchored at the page
  origin, so neighbouring areas have the same phase.
- Adds a **100 mm calibration ruler** on the margin.
- Writes **one raster image at 1:1 into an A4 PDF** (210×297 mm, interpolation off, via `PDF::API2`).
  A single raster is more predictable in print than vector art, because PDF viewers and drivers smooth
  images differently.

## Step 6: Verification

- **Automatic (`oid_check`):** in every coded area, measures the period of the dot pattern (autocorrelation
  or FFT) and fails the build if it is not ≈1.355 mm ±1 %.
- **Physical:** measure the printed 100 mm ruler - if it is shorter, the page was printed with scaling.
  Always print at **"Actual size / 100 %"**.
- **Test sheet:** the same code at 600 and 1200 dpi and with several dot size variants, plus fields with the
  code over dark color mixed from CMY and over black. Print it on your printer, check with the pen which field
  reads best, and set that as the default in `print:`.
- **Pen test mode** (pen 2.0, from [the firmware document](../en/albituzka_firmware.md#test-mode)): switch the
  pen on while holding the power and Vol+ buttons. The pen then reads OID codes and speaks them as decimal
  numbers (in Chinese). This checks a printed code without building a `.bnl`: tap a field and hear whether it
  reads and which number it is. Not verified yet whether it speaks the raw (printed) or the internal code.

## Tools (all free)

| Purpose | Tool |
|---|---|
| Drawing, mask export, rendering | Inkscape |
| Scripts | Perl with `YAML`, `Imager`, `PDF::API2` |
| Voice | `say` (macOS), later Piper |
| Audio processing | `lame`, `ffmpeg` |

## Stage 1 scope

1. Inkscape conventions + `svg_import` -> `objects.yaml` and masks.
2. `book_gen` -> `bnl.yaml` and recognition recordings (`mode_0`) with `say`.
3. `page_composer` -> A4 PDF with unscaled OID codes and the calibration ruler.
4. `oid_check` + printer test sheet.
5. A sample scene "Na wsi" (cow, hen, pig, cat, barn, sun + pen buttons) as test data for the whole pipeline.

Later stages: categories (facts, sounds, quiz), Piper voice, Wikipedia/Freesound/Ollama providers,
detectors for flat images. The pen also supports recording the child's own voice, a "compare" button and a
volume slider (codes in the BNL format document) - candidates for later.

## Open questions

- Printer type and native resolution - decided after printing the test sheet.
- Does the pen test mode speak the raw or the internal code?
- Does the printer driver print dark colors of the artwork without black (CMY only)?
