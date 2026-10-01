# Creating your own book

This guide walks through creating a custom book for the Albi pen: from sound recordings to a printed
book and a `.bnl` file for the pen. The sample book in [test/](../test/) was made this way and is a good
reference for anything not covered here (e.g. quizzes).

## Overview

A book consists of two parts:

1. **The `.bnl` file** - all sounds of the book plus the table saying which printed code plays which sound.
   It is built by `bnl_creator.pl` from:
   - your **mp3 files**
   - **`bnl.yaml`** - the only configuration file you write
2. **The printed pages** - your pictures with invisible OID codes laid over them. The pen reads the code
   under its tip and plays the matching sound from the `.bnl` file.

```
mp3 files + bnl.yaml --bnl_creator.pl--> book.bnl            --> copy to the pen
                                     \-> generate_oids.yaml  --oid_png_generator.pl--> oid_*.png --> lay out and print
```

## How the pen selects a book

OID codes are **not unique across books**. Every book numbers its codes from 0 and all official books
use codes from 10000 upwards, so the same code (e.g. 10000) exists in many books and means something
different in each. The pen only reads the code number and plays the sound from the book that is
**currently open**.

The book is chosen by its **`book_id`**, not by OID codes and not by the file name. According to the
firmware analysis in [mapfile.def](../tools/firmware_disasm/mapfile.def):

- `count_books__preload_50_book_ids` scans the `.bnl` files on the pen and preloads their book ids,
- `get_book_id_from_header` reads the book id from the file header (the file name is not used),
- `find_book` opens the file with the matching book id when the book's start icon is tapped
  (the start icon carries the `book_id` as its OID code),
- `book_ctx` holds exactly one open book at a time.

Consequences:

- **Until the start icon of a book is tapped, the pen keeps playing sounds from the previously
  opened book.** Tapping a page of a new book without activating it first plays wrong sounds.
- Every book must have its **start icon printed**, otherwise it cannot be activated.
- `book_id` **must be unique** among the books on the pen - with a duplicate, the pen may open
  the other book instead of yours.
- The function name suggests the pen preloads at most **50 book ids**, so with more than 50 `.bnl`
  files on the pen some books may not be found (not verified on a real pen).

## What you need

- **Perl 5** with these modules:
  - `YAML` - for `bnl_creator.pl`
  - `Imager` (includes `Imager::Fill`) - for `oid_png_generator.pl`

  Check with `perl -MYAML -e1` and `perl -MImager -e1`; install missing ones with `cpan YAML` / `cpan Imager`.
- **A sound editor** (e.g. Audacity) to record and cut the sounds into mp3 files.
- **A graphics editor** (e.g. GIMP, Photoshop) to lay out the pages and place the OID codes.
- **A printer**, ideally a laser printer at 1200 dpi. Printing quality decides whether the pen can read the
  codes - see [Printing tips](#printing-tips).

## Step 1: Prepare the sounds

Every sound the pen plays is a separate mp3 file. Put all of them into one working directory -
`bnl_creator.pl` looks for the mp3 files in the directory it is run from.

- Use plain file names without spaces or diacritics, e.g. `hen.mp3`, `welcome.mp3`.
- Official books use CBR mp3 at 44.1 kHz, mostly 64-96 kbps (see `albituzka_soft.xlsx`).

## Step 2: Write bnl.yaml

`bnl.yaml` has three sections separated by `---` lines, always in this order:

1. **header** - book number, start sounds, modes, encryption
2. **quiz** - quiz definitions (may be empty)
3. **oids** - which code plays which sound

### Minimal template (no quiz)

```yaml
---
#book number (701-9999), its OID is printed on the book's start icon
book_id: 0x1F40

#built-in pen icons you want to print in the book (volume_up, volume_down, stop, compare)
sys_icons:
  - volume_up
  - volume_down
  - stop

#keep as is - leaves the book effectively unencrypted
encryption:
  header_key: 0x00000100
  prekey: [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
  prekey_dw: 0x000000F5

#sound announcing the mode when a mode icon is tapped
book_mode_read:
  mode_0:
    - mode_reading.mp3

#sound on the first tap of the book's start icon
start_button_1st_read:
  mode_0:
    - welcome.mp3

#sound on the second tap of the book's start icon
start_button_2nd_read:
  mode_0:
    - welcome_again.mp3

---
quizes: []

---
oid_0:
  mode_0:
    - welcome.mp3

oid_10000_hen:
  mode_0:
    - hen.mp3

oid_10001_rooster:
  mode_0:
    - rooster.mp3
```

### Header fields

- **`book_id`** - number of the book, 701-9999 (decimal or hex, e.g. `0x1F40` = 8000).
  The pen opens the book by this number when the book's start icon is tapped
  (see [How the pen selects a book](#how-the-pen-selects-a-book)).
  **Use a number no official book uses.** Official books listed in
  [albituzka_soft.xlsx](albituzka_soft.xlsx) use numbers between 810 and 4020, so a number
  from 8000-9999 is a safe choice. Also use a different number for each of your own books.
- **`sys_icons`** - built-in pen functions: `volume_up`, `volume_down`, `stop`, `compare`.
  They do not need any sound; they are listed only so that their codes get generated for printing.
- **`encryption`** - copy it from the template.
- **`book_mode_read`**, **`start_button_1st_read`**, **`start_button_2nd_read`** - sounds for mode icons and for the start icon.

### Modes

Each code can play a different sound in each mode, e.g. mode 0 reads the text and mode 2 tells
more information. Modes are written as `mode_0`, `mode_1`, `mode_2`, ... inside every entry. The number
of modes of the book is taken from the highest mode used anywhere in the file.

Mode 0 is the default one. Modes 0 and 1 behave as one pair - the pen switches between them when
the same code is tapped twice. See `book_mode_read` in [test/podklady/bnl.yaml](../test/podklady/bnl.yaml)
for a book with more modes.

### OID entries

Each entry in the third section binds one code to sounds:

```yaml
oid_10000_hen:        #code 10000, "_hen" is just a description for you
  mode_0:
    - hen.mp3         #one or more files, played one after another
  mode_2:
    - hen_facts.mp3
```

- The name has the form `oid_` + number + optional `_description`. The number is decimal
  (`oid_10000`) or hex with an `x` (`oid_x2710`). The description is ignored by the pen, but it becomes
  part of the generated PNG file name, so it helps you find the right code when laying out the pages.
- **Use codes from 10000 upwards for your own content.** Codes 100-499 are used by quizzes;
  lower codes are system codes. The same numbers are used by other books too - that is fine,
  because only the currently open book is used.
- `oid_0` should play the same sound as `start_button_1st_read` (the sample book does this too).

### Quizzes

Quizzes are optional; with `quizes: []` the build prints a harmless warning `zero length of quiz tables!`.
If you want a quiz, copy the quiz section and the related OIDs from
[test/podklady/bnl.yaml](../test/podklady/bnl.yaml) and adapt them. Note that quiz type 0
uses keys `q0_oid`, `q0_unk` and `q0_good_reply_oids`.

## Step 3: Build the .bnl file

Run in the working directory with your mp3 files and `bnl.yaml`:

```sh
perl /path/to/repo/tools/creator/bnl_creator.pl -input bnl.yaml -output my_book.bnl
```

The output ends with `Created my_book.bnl, ... bytes long.` and `Done.` It also creates
**`generate_oids.yaml`** - the list of all codes you need to print:

- the book's start icon (code = `book_id`)
- the `sys_icons`
- the mode icons (for books with more than one mode)
- quiz icons
- all your codes from 10000 upwards

Read the warnings: the tool reports missing mp3 files, mp3 files not used by any code and references
to codes not defined in the oids section.

## Step 4: Generate OID codes

```sh
perl /path/to/repo/tools/oid_generator/oid_png_generator.pl @generate_oids.yaml
```

This creates one PNG file per code, named after the entry, e.g. `oid_10000_hen.png`, `oid_icon_start.png`.
Options:

- `-size N` - size of the code area in millimeters (default 20), or `-sizex N` / `-sizey N` separately
- `-dpi N` - 600 or 1200 (default 1200)

A single code can be generated with `oid_png_generator.pl 10000 -output hen.png`.

## Step 5: Lay out and print the pages

1. Put your pictures on the pages in a graphics editor.
2. Place each OID PNG over the area the pen should react to (see [test/final/slepicka.png](../test/final/slepicka.png)
   for an example). Keep the PNGs at their original resolution; do not scale them.
3. Print in **black and white, 1200 dpi, A4, centered, without any scaling** ("actual size").
   Printer scaling or "fit to page" changes the code pattern and the pen will not read it.

**Print a test page first** with a few codes and check that the pen reads them before printing the
whole book. See [test/final/](../test/final/) for print-ready pages of the sample book.

### Printing tips

The pen reads the dots in infrared. It sees practically only carbon-based black (black toner, pigment black
ink); color inks and toners are mostly invisible to it. The tips below come from general experience with
OID codes (mostly the Tiptoi community), not from the Albi documents - verify them with a test page.

**Printer type:**

| Printer | Chances | Why |
|---|---|---|
| Mono laser, 1200 dpi | very good | carbon toner, sharp dots |
| Mono laser, 600 dpi | usually good | generate the codes with `-dpi 600`, so the printer does not resample them |
| Color laser | good | color toners are invisible to the pen, so the artwork does not cover the dots |
| Inkjet | varies | pigment black ink works, but ink spreads in paper and dots grow; some printers mix black from colors, which the pen cannot see |

**Settings:**

- Generate the codes at the printer's **native resolution** (`-dpi 600` or `-dpi 1200`). A mismatch makes the
  driver resample the page and blur or drop the dots.
- **Actual size / 100 %**, no "fit to page", no "shrink oversized pages", no borderless printing.
- **Highest quality**, no toner/ink saving or draft mode.
- On an inkjet, choose the mode that prints black with the black cartridge (e.g. "black ink only" or
  "grayscale", if the driver offers it). The artwork will then be grey as well.

**Paper:** matte office paper, preferably thicker (100–120 g/m²). Photo and glossy paper usually do not work.

**Artwork:**

- Keep the pictures under the codes light; large dark areas hide the dots (the sample book lightens photos
  under codes to 40 % of their darkness).
- In color printing, dark areas mixed from colors (CMY) do not disturb the codes, but black ink/toner
  does. The printer driver decides how dark colors are printed - check it on the test page.

**Checking the print:**

- Print a 100 mm line next to the codes and measure it. If it is shorter, the page was scaled.
- Pen 2.0 has a hidden **test mode**: switch it on while holding the power and Vol+ buttons. The pen then
  speaks every OID code it reads as a decimal number (in Chinese), so you can check the print without
  building a `.bnl` file. See [the firmware document](en/albituzka_firmware.md#test-mode).
- Quickest check whether your printer is suitable at all: print [test/final/slepicka.pdf](../test/final/slepicka.pdf),
  copy [test/final/slepicka.bnl](../test/final/slepicka.bnl) to the pen and tap the pages.

## Step 6: Copy the book to the pen

Connect the pen to a computer via USB. Copy your `.bnl` file to the pen the same way as the official
`.bnl` files downloaded from the Albi websites (see [README.md](README.md) for the download pages):
look where the official `.bnl` files are stored on your pen and put yours next to them.

The file name does not matter - the pen reads the `book_id` from the file header (official files have
arbitrary names, e.g. `swiat-zwierzat.bnl`). Keep in mind the limit of about 50 books described in
[How the pen selects a book](#how-the-pen-selects-a-book).

**Always tap the book's start icon first**, then the pages. Without it the pen stays in the previously
opened book and plays its sounds.

For more details on this step see the article (in Czech)
https://tatageek.blog/2022/03/28/jak-vytvorit-vlastni-knizku-pro-albi-tuzku/

## Troubleshooting

| Message | Cause |
|---|---|
| `Book id ... is out of range (701-9999)` | `book_id` outside the allowed range |
| `Input file references sound file '...' which is not there` | mp3 file missing in the working directory, or a typo in its name |
| `warning: there is unreferenced file in media dir` | an mp3 file is not used by any entry - harmless, but may be a typo |
| `warning: there is a reference to OID ... not present in oid table` | a code used in the header or quiz is not defined in the oids section |
| `Duplicate oid definition` | the same code number is used twice (e.g. `oid_10000_a` and `oid_x2710`) |
| `Invalid oid format` | entry name does not match `oid_<number>[_description]`, or a quiz uses old `q1_*` keys |
| `Expected keyword mode_X` | a typo in a `mode_N` key |
| `Can't locate YAML.pm` / `Imager.pm` | the Perl module is not installed |
| The pen does not react to a printed code | printing problem - see [Printing tips](#printing-tips): scaling, wrong dpi, too dark artwork, ink the pen cannot see |
| The pen plays sounds from a different book | the book was not activated - tap its start icon first; if it persists, another book on the pen has the same `book_id` |

To check the tools themselves, build the sample book as described in [test/README.md](../test/README.md).
