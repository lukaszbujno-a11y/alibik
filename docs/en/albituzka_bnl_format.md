# BNL file format

English translation of [albituzka_bnl_format.pdf](../albituzka_bnl_format.pdf) (Czech original, version 1.5).
jindroush@seznam.cz, vpotoček – July 2025

## Introduction

### What a BNL file contains

The information below is largely theory verified on known files, by now refined quite a lot by examining
the pen firmware.

- **Book number** – after the power-on button is tapped, the pen loads the matching file from the SD card.
- **Book modes** – every place on a page can have a different sound associated; modes are switched by
  special icons.
- **Links between OID codes and sound files.** Every OID code has as many sounds as the book has modes.
- **Quizzes** – the reverse link between the sound of a question and the OID code of the answer.
- **System global sound tables** for quizzes, sounds of system buttons, etc.
- **MP3 sound files.**

### Book modes explained

- If the mode is set to 0, the pen alternates between sounds 0 and 1 for the same object on the page.
- If the mode is higher, the pen wants to play the sound at position MODE, or it simply searches further
  through all OIDs in the table. So if an object should not react, it is not enough to set a zero OID – it
  must be associated with an empty sound.

### Order of the blocks in the file

The order of the blocks matches the layout of the distributed BNL files.

- Header with pointers to other structures and some constants
- Offset table (conversion of OID codes to sounds)
- Quiz table, linking the quiz intro with questions and correct answers
- OID tables
- Sound tables
- Table of offsets of MP3 files
- Encrypted MP3 files

### Number formats

- 8-bit (BYTE)
- 16-bit little-endian (WORD)
- 32-bit little-endian (DWORD)
- all pointers are absolute DWORDs from the start of the file
- all numbers are assumed to be unsigned
- **OID** is the internal code of the pen, either converted from the raw code read from the dots on paper,
  or a virtual code used in a quiz. Always a WORD.
- **MediaId** is an index into the table of MP3 files, indexed from 0, WORD.

## OID codes

The Albi pen uses OID 2.0 codes. Their value is a WORD, so it ranges from 0x0000 to 0xFFFF, although in
some places of the firmware it is processed as a DWORD.

*[placeholder in the original: "images about the construction of the OID 2 code go here"]*

The value on paper, i.e. the **raw code**, is converted for an unknown reason and in an unknown place to an
**internal code**, which the pen then processes. The purpose of this oddity is currently unknown; in any
case there is a 65,536-row table that converts raw codes to internal ones.

## Header

The header is 0x200 (512) bytes long. Unused places contain 0xFFFFFFFF. Pointers are encrypted.

| Offset | Type | Description |
|---|---|---|
| 0x0000 | DWORD | **header_key** – all pointers in the header are XORed with it; the highest byte is also used to derive the MP3 encryption key. This DWORD contains two linked bytes – the first and the last. The second and third bytes contain the number of quizzes (WORD shifted 8 bits left). The first byte plus the last byte of the DWORD at 0x140 must give 0xF5. |
| 0x0004 | DWORD | ? – pointer to the first value of the OID code table. 0x200 in all examined files. When this value was changed, the pen never recognized the resulting file (tried ±DWORD, 0x300 and 0x400). |
| 0x0008 | DWORD | Pointer to the table of offsets of MP3 files |
| 0x000C | DWORD | Pointer to a sound table – played on the first tap of the Start button |
| 0x0010 | DWORD | Pointer to a sound table – played on the second tap of the Start button |
| 0x0014 | DWORD | Pointer to a sound table – sound when the book is "closed" – how? |
| 0x0018 | WORD | Always 0 in official files. Experiments showed it is the lowest element of the offset table, i.e. the base of the offset table. |
| 0x001A | WORD | Last used OID code. The length of the offset table is therefore (last − base + 1). |
| 0x001C | WORD | Number of used media files – unfortunately not exactly right, usually somewhat lower than the number of real, used MP3 files. According to experiments the pen does not mind setting it to the "real" number of MP3 files. |
| 0x001E | WORD | ? – always 0. Experiments did not show any effect of any value here. Probably padding of the previous WORD. |
| 0x0020 | DWORD | Pointer to a sound table – unknown purpose |
| 0x0024 | DWORD | Pointer to a sound table – sound played when the mode is switched |
| 0x0028 | DWORD | ? – always FFFFFFFF |
| 0x002C | DWORD | **book_mode_read** – number of modes the book supports (probably only a WORD, upper WORD always 0 – padding?). Modes are switched by buttons such as book, light bulb, bubble; they bind one OID to several sounds. |
| 0x0030 | DWORD | ? – 5× FFFFFFFF |
| 0x0044 | DWORD | Pointer to the quiz table |
| 0x0048 | DWORD | Pointer to an OID table (played on a correct quiz answer) |
| 0x004C | DWORD | Pointer to an OID table (played on a correct quiz answer) |
| 0x0050 | DWORD | Pointer to an OID table (played on a wrong quiz answer) |
| 0x0054 | DWORD | Pointer to an OID table (played on a wrong quiz answer) |
| 0x0058 | DWORD | Pointer to an OID table (book sound played on inactivity while a quiz is running) |
| 0x005C | WORD | **Unique book number** – the raw code for this OID is printed on the Start button. |
| 0x005E | WORD | 0, padding of the previous WORD. Experiments showed its value does not matter. |
| 0x0060 | DWORD | 15× pointer to a sound table of unknown use (system sounds?) |
| 0x009C | DWORD | Pointer to an OID table (wrong answer and end of quiz) |
| 0x00A0 | DWORD | Pointer to an OID table (correct last answer to a question with several answers) |
| 0x00A4 | DWORD | Pointer to an OID table (for a question with several answers, this answer is already marked – not counted as a mistake) |
| 0x00A8 | DWORD | Pointer to an OID table, most often of length 6. Contains spoken quiz results (from none correct up to all 5 correct). |
| 0x00AC | DWORD | 8× 0xFFFFFFFF |
| 0x00CC | DWORD | 29× pointers to media tables of unknown use |
| 0x0140 | DWORD | Probably used for key derivation, not known exactly. The lowest byte of this DWORD plus the highest byte of header_key must be 0xF5. If set to 0xFFFFFFFF, MP3 encryption is switched off completely. |
| 0x0144 | BYTE[16] | 16 bytes forming the key for decrypting the MP3 files. |
| 0x0154 | DWORD | 0xFFFFFFFF all the way up to offset 0x200 |

## Offset table

Only a sparse list of DWORD pointers – 0xFFFFFFFF is the "empty" value. Each pointer points to a place in the
file where `book_mode_read` sound tables follow one after another. Each table has 0 or 1 sound; no longer
one has been seen. Experiments showed that more sounds in a table simply means the sounds are played one
after another. The OID is the offset into this table, which binds OID + mode to a sound. The table base
(0x18 in the header) is subtracted from the OID.

Modes 0 and 1 alternate, whether mode 0 is activated automatically after power-on or by tapping the "book"
icon – most or all books always have modes 0 and 1 identical. The switch between modes 0 and 1 happens when
the same OID is read again.

## OID table

A simple table containing a WORD item count N followed by N WORD OIDs.

## Sound table

A simple table containing a WORD item count N followed by N WORD sound indexes.

## Quiz table

The most complicated and least explored part of the BNL file, with the biggest open questions so far.

It starts with a list of DWORD pointers to the individual quiz headers. Originally the length of this table
was not known – the first quiz header follows right after it, which ends the traversal; now the value from
the first DWORD of the file can be used. The number of quizzes usually matches the number of double pages of
the book, sometimes multiplied by several difficulty levels.

### Quiz types

0. standard quiz – the pen asks random questions and expects answers
1. reverse quiz – the player chooses questions and looks for answers to them
2. *[not used by Albi]* – reverse quiz, answers must be given in a fairly exact order
3. *[not used by Albi]* – like 0, reactions like quiz 2
4. extended standard quiz
5. *[not used by Albi]*
6. *[not used by Albi]*
7. *[not used by Albi]*
8. same as type 4 with a fixed order of questions
9. *[not used by Albi]*, like 4, with a time limit per question
10. *[not used by Albi]*, like 4, "off-topic" answers are indexed by their count (first mistake, second
    mistake, etc.)

Quizzes have mistake tolerances. There is one tolerance in the header; in higher types the answers
distinguish "right kind, wrong choice" from "completely off". E.g. for the question 1+1 the correct answer is
2, a wrong answer is 3 and an off-topic answer is "bat".

### Quiz header

| Offset | Type | Description |
|---|---|---|
| 0x0000 | WORD | Quiz type in the low byte. Number of tolerated mistakes in the high byte; if zero, the default 3 is used. |
| 0x0002 | WORD | Qcnt – number of possible questions of the quiz |
| 0x0004 | WORD | Number of questions asked. It must be cross-checked that the table at offset 0xA8 is always one longer than this value (all wrong up to all correct, N+1 possibilities). Theory: it follows that all quizzes must have the same number of questions set – otherwise the evaluation would not work correctly; some books have it set differently (not available to me). |
| 0x0006 | WORD | Answer evaluation, mostly 0, sometimes 1, once 2 or 5. Discovered options: 0 – finding one of the OIDs in the answer list is enough; 1 – wants all OIDs in any order; 2 – wants all OIDs in the exact order; 3 – repeats the question forever (firmware bug). |
| 0x0008 | WORD | OID leading to the sound of the quiz intro. An invalid value still starts the right quiz, just without the intro sound. Theory: so the order of quizzes is given purely by their order in the table (and is therefore hard-coded from 100), and the OID is only a link to the intro sound? |
| 0x000A | DWORD | Qcnt × DWORD pointer to individual questions |

### Quiz question, type 0

| Offset | Type | Description |
|---|---|---|
| 0x0000 | WORD | Unknown value, quite often equal to the second value; setting it to any value, even the same for all questions, made no noticeable difference – for quiz type 0. |
| 0x0002 | WORD | OID leading to the sound of the quiz question |
| 0x0004 | | Table of OIDs marking the correct answers (same format as the OID table above) |

### Quiz question, type 1

| Offset | Type | Description |
|---|---|---|
| 0x0000 | WORD | OID for the question |
| 0x0002 | WORD | Sound for the chosen question |
| 0x0004 | | Table of OIDs marking the correct answers (same format as the OID table above) |

### Quiz question, types 4 and 8

| Offset | Type | Description |
|---|---|---|
| 0x0000 | WORD | OID leading to the sound of the quiz question |
| 0x0002 | WORD | How the sound for a correct answer is chosen: 0 = randomly, 1 = by the index of the answer in the list, 2 = by the order of the correct answer. |
| 0x0004 | WORD | BOOL. If 1, answers are required in the correct order. I.e. the same as quiz header +0x06 = 2 for types 0 and 1, but for type 4 specified per question. The "global" 0x06=2 behaves the same as 0x06=1 – both just require all answers. With 0x06=0 one answer is enough. If quiz[0x06]=0 and at the same time question[0x04]=1, which is a bit nonsensical, it must be the first one. |
| 0x0006 | WORD | Tolerance of the number of wrong answers. If 0, the default 3 is used. (The tolerance of "off-topic" answers is taken from quiz header +0x01 as usual.) |
| | | Table of OIDs marking the correct answers |
| | | Table of OIDs, list of wrong answers (not used by Albi) |
| | | Table of OIDs, sound of a correct answer. Should be one longer than the number of answers; the last OID should be the sound prompting to continue. |
| | | Table of OIDs, sound of a repeated correct answer; one random one is played |
| | | Table of OIDs, sound of a wrong answer; should be as long as the list of wrong answers – every wrong answer has its own "comment". |
| | | Table of OIDs, sound for a "completely off" answer |
| | | Table of OIDs, sound of the positive final evaluation |
| | | Table of OIDs, sound of the negative final evaluation |

## MP3 files

### Table of MP3 file offsets

A table for N MP3 files – just N+1 DWORD offsets pointing to the start of each MP3 file; the last DWORD is
the length of the whole file (and so the end of the last MP3 file). MP3 file starts are aligned to multiples
of 512; the padding after the end of the previous MP3 file is repeated zero bytes. The end is not aligned.

### MP3 key

MP3 encryption uses a 16-byte key. Its value is created by adding the highest byte of header_key to the
16 bytes (the intermediate key) stored in the header from address 0x144.

At address 0x140 there is a so far mysterious value from which the generation of the intermediate key
starts. The value is relatively low, often left-padded with zeros, so it looks like some pointer or sum.
It has not yet been found what this value correlates with.

At address 0x144 there are 4 DWORDs:

- DWORD 1 – so far generated in an unknown way from the value at 0x140 (quite often bytes 2 are the same and
  bytes 3 similar); the first and last bytes are then linked via the table TblUnk2 [to be corrected?] from
  the firmware.
- DWORD 2 – three times DWORD 1, truncated to 32 bits.
- DWORD 3 – integer result of DWORD 2 divided by five.
- DWORD 4 – DWORD 3 plus two.

Comment: It is completely incomprehensible why the intermediate key is stored in the BNL file when it is
algorithmically easy to generate. This practically invites easy decryption, because DWORD 1 almost always
contains 0, so it is easy to deduce that the byte from header_key must be added. Moreover, because the
intermediate key is stored in the file, the whole key is easy to derive, especially given that DWORD 3 and
DWORD 4 are practically the same. All wrong (all good for reverse engineering).

### MP3 encryption

Encryption works like this:

Take the 16 bytes stored in the header from offset 0x144 and add the highest byte of header_key to each.
A sparse key of 512 (0x200) bytes is generated so that:

- for every 16 bytes, 4 bytes of the key from the header are used; they are placed at offsets 0 to 3 from a
  number divisible by 4,
- i.e. every 64 bytes the whole 16-byte key from the header is used exactly once,
- this is repeated in 8 blocks.

Offsets 0 to 3 are stored in the firmware at an address I provisionally named
`tbl_mp3_encryption_offsets`. Before I found it, I manually assembled a table that works for all BNL files.

The table below has one row per byte of the input key; each row says which offset from a number divisible
by 4 the key byte has in each of the 8 blocks.

So the first byte of the input key is stored at offsets 0x00, 0x41, 0x81, 0xc2, 0x100, 0x141, 0x181, 0x1c2.
The second byte at offsets 0x07, 0x47, 0x86, 0xc5, 0x105, 0x146, 0x186, 0x1c5.

```
[0,1,1,2,0,1,1,2],
[3,3,2,1,1,2,2,1],
[2,2,3,1,2,2,3,1],
[1,0,0,0,1,0,0,0],
[1,2,0,1,1,2,0,1],
[1,2,0,2,1,2,2,2],
[2,1,0,0,2,1,0,0],
[2,3,2,2,2,3,2,2],
[3,0,3,1,3,0,3,1],
[0,0,1,1,0,3,1,1],
[2,2,3,0,2,2,3,1],
[3,1,0,0,3,1,0,0],
[3,3,0,2,3,3,1,2],
[1,2,0,0,1,2,0,0],
[2,1,0,3,2,1,3,3],
[0,0,0,0,0,0,0,0]
```

So:

```
key[ block * 0x40 + key_ofs * 4 + table_above[key_ofs][block] ] = input_key[key_ofs];
```

This key is then XORed with every byte of the MP3 file. Skipped are the bytes 0x00, 0xFF, a byte equal to the
key byte (because the XOR would give 0x00) and a byte equal to the key byte XOR 0xFF.

The same procedure is used for both encryption and decryption.

## Default values

The numeric values of OIDs are certainly divided into several groups. Originally this division was derived
from existing files; later, after a successful analysis of the table at the start of the third part of the
firmware, it was clarified further.

- **Book code** was observed from 0x32A to 0xCFC; the firmware analysis then narrowed it to **0x2BD (701)
  to 0x270F (9999)**.
- **Quizzes** (their "intro questions" and the codes printed on dice icons) mostly start from 0x64 (100).
  Some quizzes lead to non-existent OIDs of intro sounds – it looks like the pen then plays no sound.
  According to the firmware analysis, quizzes start at **0x64 (100) and go up to 0x1F3 (499)**.
- OIDs in OID tables: 0x190–0x1BD, exceptionally 0x1F4–0x221.
- Most codes on the first page of a book start with OID 0x2AF8 (11000), 0x2AF9, 0x2AFA. "Učitel" (Teacher)
  starts at 0x283D, "Dinosauři" (Dinosaurs) at 0x2711 (10001). OID codes for physical book pages quite often
  start at such round decimal numbers. Given that the book number range ends at 9999, we can estimate that
  **user codes start at 0x2710 (10000)**.

### Built-in button codes

| Icon | Raw code on paper | Internal code | Firmware code |
|---|---|---|---|
| Start | raw book id | 0x02BD–0x270F | 0x0010 |
| Vol+ | 0x0015 | 0x0007 | 0x0030 |
| Vol− | 0x0016 | 0x0008 | 0x0031 |
| Stop | 0x0014 | 0x0006 | 0x0080 |
| Compare | 0x0531 | 0x0063 | 0x0050 |
| Repeat last sound | | 0x0009 | 0x0504 (or 0?) |
| MP3 mp3 | 0x0141 | 0x002E | 0x0040 |
| MP3 play | 0x0143 | 0x002F | 0x0043 |
| MP3 pause | 0x0150 | 0x0030 | 0x0042 |
| MP3 stop | 0x0151 | 0x0031 | 0x0044 |
| MP3 prev | 0x0153 | 0x0032 | 0x0045 |
| MP3 next | 0x0180 | 0x0033 | 0x0046 |
| WAV Record 001–300 | | 0xEA61–0xEB8C | 0x3000–0x312B |
| WAV Record 301–999 | | 0xF231–0xF4EB | 0x312C–0x3257 |
| WAV play 001–300 | | 0xEB8D–0xECB8 | 0x4000–0x412B |
| WAV play 301–999 | | 0xF4ED–0xF7A7 | 0x412C–0x43E6 |
| WAV OK any | | 0xECB9–0xEDE4 | 0x7000 |
| WAV OK any | | 0xF03D–0xF168 | 0x7001 |
| Audio block REC (bookidRecXXX.wav) | | 0xEDE5–0xEF10 | 0x5000–0x512B |
| Audio block PLAY | | 0xEF11–0xF03C | 0x6000–0x612B |
| Mode 1 / Open book | 0x000C | 0x0004 | 0x0093 |
| Mode 2 / Light bulb / Play | 0x000F | 0x0005 | 0x0094 |
| Mode 3 / Bubble | 0x0007 | 0x0003 | 0x0092 |
| Mode 4 / Note / Czech translation (basic info) | 0x0006 | 0x0002 | 0x0091 |
| Mode 5 / Czech translation (dialogues) | 0x0005 | 0x0001 | 0x0090 |
| Mode 6 | 0x25CF | 0x0225 | 0x0095 |
| Mode 7 | 0x25D5 | 0x0226 | 0x0096 |
| Mode 8 | 0x25DA | 0x0227 | 0x0097 |
| Mode 9 | 0x25DF | 0x0228 | 0x0098 |
| Mode 10 | 0x25FC | 0x0229 | 0x0099 |
| Mode 11 | 0x2800 | 0x022A | 0x009A |
| Mode 12 | 0x2819 | 0x022B | 0x009B |
| Volume (volume slider) | x | 0x000A–0x0019 | 0x0020–0x002F |
| Recording own sound | | 0xCB3A | 0x60 |
| Stop recording | | 0xCB3B | 0x61 |
| Play all REC | | 0xCB3C | 0x62 |
| Calculator, start | | 0xCB72 | 0x81 |
| Calculator, 0–9, +, −, *, /, =, C | | 0xCB73–0xCB81 | 0x82 ? |
| English spelling, probably somehow related to dictionaries (?) | | 0x1F5–0x20E | 0x2003–0x201C |

There are many other internal firmware codes, but their meaning is not known yet:

- 0x2000–0x201C (0x2003–0x201C known)
- 0x48–0x4A
- 0x60–0x62
- 0xF01–0xF16
- 0x70–0x77 (in newer firmware, without 0x73)

Further OID ranges in the main conversion function – this evaluation is done first, and only then is the
encrypted table in the third part of the firmware consulted. The reason for duplicating the same thing in
code and in the table still escapes me.

```
0xFE11 = 0x31 -> vol-
0xFE12 = 0x30 -> vol+
0x9 = 0x504
0xCB3A = 0x60
0xCB3B = 0x61
0xCB3C = 0x62
0xCB83 = 0x108
0x34-0x3A = 0x100-0x106
0xCB54-0xCB5A = 0x100-0x106
0x1E, 0xCB52 = 0x109
0x1F, 0xCB53 = 0x10A
0x50, 0xCB70 = 0x10B
0x51, 0xCB71 = 0x10C
0x3C-0x4F = 0x300-0x313
0xCB5C-0xCB6F = 0x314-0x327
0xEA61-0xEB8C = 0x3000-0x312B
0xF231-0xF4EB = 0x312C-0x3257
0xEB8D-0xECB8 = 0x4000-0x412B
0xF4ED-0xF7A7 = 0x412C-0x43E6
0xEDE5-0xEF10 = 0x5000-0x512B -> wav record?
0xEF11-0xF03C = 0x6000-0x612B -> wav play?
0xECB9-0xEDE4 = 0x7000
0xF03D-0xF168 = 0x7001
0x52,0xCB72 = 0xE6
0x62,0xCB82 = 0xEF
0x5D-0x61 = 0xE8-0xEC
0xCB7D-0xCB81 = 0xE8-0xEC
0x53-0x5C = 0xF0-0xF9
0xCB73-0xCB7C = 0xF0-0xF9
0xD2F1-0xE14A = 0x403 -> songs?
0x215 = 0x501
0x216 = 0x502
0x217 = 0x404
0x218 = 0x405
0x219 = 0x406
0x21A = 0x407
0x21B = 0x408
0x21C = 0x503
```

Codes not yet clarified and processed can be described in the Google sheet linked in the original document.

## History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2.2.2022 | Jindroush | first version |
| 1.1 | 21.2.2022 | Jindroush | button codes added |
| 1.2 | 5.3.2022 | Jindroush | more precise code ranges added |
| 1.3 | 7.4.2022 | Jindroush | more code ranges added |
| 1.4 | 24.6.2025 | Jindroush | incorporated notes by Vašek Potoček from issue 4: meaning of byte 6 in a quiz (reported earlier by Honza Janovský on TataGeek, unfortunately not incorporated in time), internal code 9 (reported earlier by darinas), calculator codes (partly reported by darinas), range corrected up to 0x77, system sounds and the table at 0x14, explanation of the intermediate key generation added. Link to the Google sheet added. Some minor changes to the quiz description. |
| 1.5 | 23.7.2025 | Jindroush | document outline changed, heaps of notes by Vašek Potoček about quizzes incorporated. |
