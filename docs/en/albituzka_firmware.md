# Firmware of the Albi pen

English translation of [albituzka_firmware.pdf](../albituzka_firmware.pdf) (Czech original).
https://github.com/jindroush/albituzka

Translation notes:

- Chinese texts were transcribed by the original author with AI (Whisper) and translated with Google
  Translate; the bracketed English renderings below come from the original.
- The string table of the first firmware part (pages 11–77 of the original, ~3,650 entries, almost all
  Chinese) is not reproduced in full – see [String table](#first-firmware-part-texts-old-firmware) for a
  summary and the translated entries.

## Version overview

Some firmware files were downloaded from Albi, some from Archive.org, some from "the internet".

| Lng | HW | V1 | V2 | MD5 |
|---|---|---|---|---|
| CZ | SNC7003 | ZC-p15095V04 | 20140409V004 | 91b3f774c6761ffe966f39fcb2535776 |
| CZ | SNC7003 | ZC-p15095V03 | 20150602V003 | 628ebdd386e59d9e610b3f4f50bdb3bb |
| CZ | SNC7003 | ZC-p15095V03 | 20150602V003 | 4f3118e645d97fbff85f843515fe35ee |
| SK | SNC7003 | ZC-p15095V08 | 20160516V008 | a1566fdf60fc07000dfe0f1dda86260c |
| CZ | SNC7003 | ZC-p15095V08 | 20160516V008 | 427c7a1fdf2c6f8bdff138726869dc31 |
| CZ | SNC7003 | ZC-p15095V09 | 20161220V009 | cc145d1e29eca38d3810fe2dca4c14d2 |
| CZ | SNC7003 | ZC-p15095V09 | 20161222V011 | 564b1e03edc39a34ea6abe9c8d4f83c6 |
| SK | SNC7003 | ZC-p15095V09 | 20161222V011 | e27181bd0a31b71d78083a8dcd1574c9 |
| CZ | SN95302 | ZC-p17264V03 | 20180530V006 | c0301d6e17bf5530fc0828dd9490ca29 |
| SK | SN95302 | ZC-p17264V03 | 20180530V006 | 1dd33d1606859ae9879eddba2762065e |
| CZ | SN95302 | ZC-p17264V03 | 20240517V019 | 9a603c5518872185abece57738b9f6c6 |
| PL | SN95302 | ZC-p17264V03 | 20240517V019 | 17b8b474b7b98d26a36ef7fd0f17ae52 |
| CZ | SN95302 | ZC-p20115V01 | 20240530V023 | 8c693d1d05f8865eb413bdb45715a6a3 |
| PL | SN95302 | ZC-p20115V01 | 20240530V023 | 0484cf2df394af0a16958aadc76c7341 |

## Pen versions

If I understand the information on the Albi website, there are three hardware versions:

1. Pen 1.0, 2014–2017 (E8800). Most likely runs on SNC7003.
2. Pen 1.0, 2018+ (E8800). Serial number after the dash 8, 9, A, B, C. Already runs on SN95302. Has only
   micro USB.
3. Pen 2.0 (R50). From about 2022/5. The hardware description is in the separate document
   [albituzka_hw2.md](albituzka_hw2.md).

## Internal structure

The firmware is in the files `update.chp` or `updateA.chp`. It starts with some header followed by several
pointers. From the Sonix SoC documentation I concluded that the whole file is mapped into external memory
from 0x00400000 and is addressed by WORDs.

| Offset | Size | Meaning |
|---|---|---|
| 0xA0 | DWORD | Start of the second part (pointer in WORDs, from 0x00400000) |
| 0xA4 | DWORD | End of the second part |
| 0xA8 | DWORD | Start of the third part |
| 0xAC | DWORD | End of the third part and so the length of the whole CHP file |
| 0xB0 | DWORD | Unknown, changes between firmwares, but only "slightly" |
| 0xB4 | DWORD | Pointer to the textual version information, 0x00400300 everywhere |

PRAM table – always starts at 0x400080 (i.e. 0x100 in the file):

| Offset | Size | Meaning |
|---|---|---|
| 0x100 | BYTE[8] | String with the pen chip name, reversed. The ROM bootloader checks that the firmware is meant for it. |
| 0x108 | WORD | Number of following "modules", always one for Albi |
| 0x10A | WORD | Module ID, the first always 0x8001. Purpose not found. |
| 0x10C | WORD | Length of the PRAM memory |
| 0x10E | DWORD | Pointer to the part of ROM that is copied into PRAM. Code always starts at the beginning of PRAM, i.e. address 0x4000. In the Albi firmware there is an interrupt table there; the first jump is a jump to SysMain. |
| 0x112 | DWORD | Address of the PRAM memory – always 0x00004000; the interrupt table is at this address, the first vector is a jump to main. |
| 0x116 | DWORD | Sum of all WORDs of the PRAM memory. If it does not match, the bootloader refuses to load the module. |

The first part of the firmware implicitly starts at 0x00400000 and ends at the start of the second part; it is
aligned to a length of 512 KB.

These three parts exist as separate files in the BurnFile directory (whether they are combined into
`update.chp` or unpacked from it, I do not know).

**1.bin** contains:

- the header
- the version
- all the code
- a text table (extracted below)
- some other tables and strings of unknown purpose

The code is about 230 KB long and it is quite certain it contains only the routines handling the BNL file.
All MP3, SD card, FAT etc. processing is in the chip's ROM, so analysing the code is an even harder nut to
crack, because it contains jumps into ROM without it being clear which functionality is being called.

The text table obviously contains names of some songs, but I have no idea whether and where the firmware
should contain these melodies. Most names are in Chinese, a few in English. The table has over 3,500 entries,
so it seems unlikely to me that that many songs could be anywhere in the firmware – and I do not know what
the names are for, when the pen has no text/image output. One possible theory is that the firmware (or its
source code) is shared between several products which have e.g. a display. A brief look into the code
suggests that OIDs 54001–57674 start playing a file XXXXX.tn2.

**2.bin** contains only a large number of MP3 files, practically all in Chinese.

**3.bin** contains:

- At the start a data block of 0x10000 bytes, constructed so that each block of 0x100 bytes contains every
  byte exactly once, visibly with 0xFF at the last position, randomly placed. This block differs in every
  firmware – it is a so-called one-time pad used to decrypt the next block.
- Then 0x10000 WORDs, where both bytes of a WORD are XORed with a byte from the previous block – the first
  word with the first byte, the second word with the second byte, etc. The bytes 0x00, 0xFF, the key and the
  key XOR 0xFF are skipped. The content is the conversion table from internal OID codes to the firmware's own
  action codes – this should handle the branching in the code for the "built-in system" buttons.
- Further data at fixed offsets 0x30000, 0x30200, 0x30300, one of them being
  `CHOMPTECH OCF FORMAT CopyRight 2012 Ver3.3.0206`.
- Right after that, from 0x30340, there are three/four DWORD pointers from the start of 3.bin to the 3/4
  following tables (the first is always at offset 0x30400):
  - MP3 table #3.1
  - table of unknown values
  - MP3 table #3.2
  - table of strings (where to look for which files)

The SD card in the pen also contains the file `SystemVoiceData.bin`, which I considered identical to the
second part of the firmware because of its length, but in fact it only contains the numbers from 1 to 100 read
in Czech. It is currently not certain whether this file still makes sense, since the calculator seems to have
been removed from the new firmware.

I originally analysed the data from the second Czech firmware (628ebdd386e59d9e610b3f4f50bdb3bb); newer
information comes from the latest firmware (8c693d1d05f8865eb413bdb45715a6a3).

## Modifying the firmware

For a long time it was not known whether the firmware can be modified. Some experiments were done on pen 2.0,
with these results:

- The pen does not check the integrity of the firmware and I was able to replace sounds (i.e. one mp3 for
  another mp3 of the same or smaller length). I assume it will probably be possible to replace anything as
  long as logical integrity is preserved.
- The pen does not check firmware versions and updates every time it finds the file `updateA.chp` on the SD
  card. I flashed two firmwares in turn which differed from the latest Czech one in 2 mp3 files. In both cases
  the update succeeded and I verified that the changed sounds were as expected.
- A small addition – the bootloader checks the integrity of the PRAM memory and does not load a changed one.

## Test mode

When pen 2 is switched on while holding the power button and the Vol+ button for a longer time, the test mode
starts. The whole test mode is in Chinese; for documentation purposes I replaced the Chinese sounds with
English ones. After power-on you hear:

- 2/207 Test mode
- 2/231 The current program version is V 0-2-3. This information is taken from the end of "version 2" of the
  firmware.
- 2/225 The pen tip test was successful (alternative 2/224). Even with the pen tip disconnected it said the
  same message.
- 2/229 CF card test successful (alternative 2/228; I assume this is an old sound file and the SD card is
  meant).

The pen then stays in a loop in which it **reads OID codes and speaks them as decimal numbers**.

Buttons:

- Vol+ triggers 2/227 and the microphone starts listening. The result is stored on the SD card as
  `testrec.wav` and played back immediately; it is about 2 s long and tests the whole microphone – SD card –
  speaker chain.
- Vol− nothing found
- Repeat – says 2/221 "three"
- Power short – says 2/204 "reset to zero"
- Power long – says 2/226 "shutdown" and switches off

## ROM

Both chips, the one in the old pen and the one in the new one, contain a 64 KW (128 KB) ROM with service
library routines. This ROM is not published; the documentation has only some routine headers, while e.g. the
whole ABI and its support functions are completely undocumented. This obstacle was recently overcome, and the
firmware disassembler project disassembles the ROM content as well. GitHub has code that dumps the ROM content
to the SD card. It must be compiled with `assemble.py` from the S9KE project and inserted into the existing
firmware for pen 2 – you have to find an empty place in ROM and some place to jump from. I overwrote one of the
Callff instructions in the test mode to make sure that even if the code were faulty, it would not start by
itself after the update without human intervention and brick the pen so that it could not even be updated.

## Second firmware part, sounds, old firmware

| Second part | Sound |
|---|---|
| 2-0000 | Update is finished |
| 2-0001 | Update in progress |
| 2-0002 | [jingle 1] |
| 2-0003 | [jingle 2] |
| 2-0004 – 2-0007 | [jingle 3] |
| 2-0008 | [short tune] |
| 2-0009 | [jingle 4] |
| 2-0010 – 2-0023 | [Chinese] |
| 2-0024 | [jingle 5] |
| 2-0025 – 2-0039 | [Chinese] |
| 2-0040 – 2-0070 | [silence] |
| 2-0071 – 2-0160 | [Chinese] |
| 2-0161 – 2-0190 | [silence of various lengths] |
| 2-0191 – 2-0192 | [Chinese] |
| 2-0193 | [jingle 6] |
| 2-0194 | [jingle 7] |
| 2-0195 – 2-0217 | [Chinese] |
| 2-0218 – 2-0223 | "Ej bí cí dí í ef" (A B C D E F) |
| 2-0224 – 2-0227 | [Chinese] |
| 2-0228 | The SD card cannot be read |
| 2-0229 – 2-0231 | [Chinese] |
| 2-0232 | [jingle 8] |
| 2-0233 – 2-0244 | [Chinese] |
| 2-0245 | Touch the recording button… |
| 2-0246 | The corresponding sound file cannot be found |
| 2-0247 | Touch the recording button… |
| 2-0248 | Now compare it (Compare step 3) |
| 2-0249 | Repeat it aloud (Compare step 2) |

## Second firmware part, sounds, new firmware

| Second part | Sound |
|---|---|
| 2-0000 | Update completed successfully |
| 2-0001 | The pen will be updated |
| 2-0002 | [jingle 1] |
| 2-0003 | [jingle 2] |
| 2-0004 – 2-0007 | [jingle 3] |
| 2-0008 | [short tune] |
| 2-0009 | [jingle 4] |
| 2-0010 | 百家姓 [Hundred Family Names] |
| 2-0011 | 宝宝睡前故事 [Baby Bedtime Stories] |
| 2-0012 | 宝宝童谣 [Baby Children's Rhyme] |
| 2-0013 | 成功预言故事 [Prophecy Tales] |
| 2-0014 | 成语 [Idiom] |
| 2-0015 | 弟子归 [The disciple returns] |
| 2-0016 | 儿歌说学斗唱 [Children's songs and Learn to Sing] |
| 2-0017 | 儿童EQ教育童话 [Children's EQ Education Fairy Tale] |
| 2-0018 | 儿童笑话 [Children's Jokes] |
| 2-0019 | 更读 [Read more] |
| 2-0020 | 偏独 [Individual mode] |
| 2-0021 | 录音开始 [Recording starts] |
| 2-0022 | 录音停止 [Recording stops] |
| 2-0023 | 复读 [Repeat] |
| 2-0024 | [jingle 5] |
| 2-0025 | 钢琴曲 [Piano song] |
| 2-0026 | 交响乐 [Symphony] |
| 2-0027 | 经典童话绘本 [Classic Fairy Tale Picture Book] |
| 2-0028 | 经典英文儿歌 [Classic English Children's Songs] |
| 2-0029 | 经典粤语儿歌 [Classic Cantonese Children's Songs] |
| 2-0030 | 经典中文儿歌 [Classic Chinese Children's Songs] |
| 2-0031 | 论语 [Analects of Confucius] |
| 2-0032 | 名人伟人故事 [Stories of Famous People] |
| 2-0033 | 催眠曲 [Lullaby] |
| 2-0034 | 知识 [Knowledge] |
| 2-0035 | 音樂 [Music] |
| 2-0036 | 我学 [I studied] |
| 2-0037 | 故事 [Story] |
| 2-0038 | 学习 [I learn] |
| 2-0039 | 沒有該曲目的聲音文件 [There is no audio file for this track] |
| 2-0040 – 2-0070 | [silence] |
| 2-0071 – 2-0160 | 第31页 … 第120页 [Page 31 … Page 120] |
| 2-0161 – 2-0190 | [silence of various lengths] |
| 2-0191 | 亲子床边故事 [Parent-child bedside story] |
| 2-0192 | 亲子梅雨教室 [Parent-child plum rain classroom??] |
| 2-0193 | [jingle 6] |
| 2-0194 | [jingle 7] |
| 2-0195 | 三字经 [Three Character Classic] |
| 2-0196 | 世界名著 [World Famous Works] |
| 2-0197 | 世界童话故事 [World Fairy Tales] |
| 2-0198 | 十万个为什么 [Hundreds of Thousands of Whys] |
| 2-0199 | 数学小天才 [A Little Genius in Mathematics] |
| 2-0200 | 四大名著 [Four Great Masterpieces] |
| 2-0201 | 胎教音乐 [Prenatal Educational Music] |
| 2-0202 | 唐诗 [Tang Poetry] |
| 2-0203 | 加密IC電路有問題 [There is a Problem With Encrypting IC Circuit] |
| 2-0204 | 起零 [Reset to Zero?] |
| 2-0205 | 嘿咦 [Hey Hey??] |
| 2-0206 | 低点呀 [Lower it a bit] |
| 2-0207 | 测试模式 [Test Mode] |
| 2-0208 – 2-0217 | 零 … 九 [Zero … Nine] |
| 2-0218 – 2-0223 | Ej, Bí, Sí, Dí, Í, Ef [A B C D E F] |
| 2-0224 | 比頭與主控MCU通訊不正常 [The communication between the header and the main controller MCU is not normal] |
| 2-0225 | 筆頭測試成功 [The pen tip test was successful] |
| 2-0226 | 關機 [Shutdown] |
| 2-0227 | 開始錄音 [Start recording] |
| 2-0228 | The SD card cannot be read |
| 2-0229 | CF卡测试成功 [CF card test successfully] |
| 2-0230 | Ví [V] |
| 2-0231 | 当前程序版本为V [The current program version is V] |
| 2-0232 | [jingle 8] |
| 2-0233 | 智慧经典绘本 [Classic Wisdom Picture Books] |
| 2-0234 | 中国诗乐 [Chinese Poetry and Music] |
| 2-0235 | 中国童话故事 [Chinese Fairy Tales] |
| 2-0236 | 中英双语童话 [Bilingual Fairy Tales (Chinese and English)] |
| 2-0237 | 著名广播剧 [Famous Radio Dramas] |
| 2-0238 | 自然科学小叮当 [Little Tinker: Natural Science] |
| 2-0239 | 万能博士小叮当 [Little Tinker: Dr. Know-it-all] |
| 2-0240 | 影视剧经典儿歌 [Classic Children's Songs from Film and TV] |
| 2-0241 | 英语单词顺口溜 [English Vocabulary Rhymes] |
| 2-0242 | 英语小天才 [Little English Genius] |
| 2-0243 | 益智百科小叮当 [Little Tinker: Encyclopedia Explorer] |
| 2-0244 | [jingle 9] |
| 2-0245 | [jingle 9] |
| 2-0246 | 语文小天才 [Little Chinese genius] |
| 2-0247 | Touch the recording button… |
| 2-0248 | The corresponding sound file cannot be found |
| 2-0249 | Touch the recording button… |
| 2-0250 | Now compare it [Compare step 3] |
| 2-0251 | Repeat it aloud [Compare step 2] |
| 2-0252 | [Ping] Pairing was successful |
| 2-0253 | [bubbles] |
| 2-0254 | [BimBimBam] Searching for Bluetooth devices to pair with the pen |
| 2-0255 | [silence] |
| 2-0256 | 慢一 [Slow one] |
| 2-0257 | 慢二 [Slow two] |
| 2-0258 | 慢三 [Slow three] |
| 2-0259 | 已是最快语速 [It's the fastest speaking speed] |
| 2-0260 | 正常语速 [Normal speaking speed] |
| 2-0261 | 已是最慢语速 [It's the slowest speaking speed] |
| 2-0262 | 快一 [Quick one] |
| 2-0263 | 快二 [Quick two] |
| 2-0264 | 快三 [Quick three] |

All Chinese texts were transcribed with AI (online, Whisper) and translated with Google Translate. So they may
mean something completely different – I skipped Chinese at school!

## Third firmware part, sounds from the first table, old firmware

| Third part, first table | Sound |
|---|---|
| 3-0000 | Welcome to the world of magic reading |
| 3-0001 | [power-on jingle?] |
| 3-0002 | The battery is almost empty |
| 3-0003 | I cannot read this book |
| 3-0004 | No music is loaded |
| 3-0005 | [beep] |
| 3-0006 | Ready? Touch what you want to compare (Compare button) |
| 3-0007 | Recording is finished |
| 3-0008 | Memory is full |
| 3-0009 | [ding-dong] |
| 3-0015 | [jingle] |
| 3-0020 | [ding-dong] |
| 3-0023 | I cannot read this book |

## Third firmware part, sounds from the first table, new firmware

| Third part, first table | Sound |
|---|---|
| 3_1-0000 | Welcome to the world of magic reading… [power-on] |
| 3_1-0001 | [jingle] See you soon [power-off] |
| 3_1-0002 | The battery is almost empty |
| 3_1-0003 | I cannot read this book, download the corresponding bnl file |
| 3_1-0004 | No music is loaded… |
| 3_1-0005 | [beep] |
| 3_1-0006 | Ready? Touch what you want to compare [Compare button] |
| 3_1-0007 | Recording is finished |
| 3_1-0008 | The pen memory is full, free up space on the memory card |
| 3_1-0009 | [ding-dong] |
| 3_1-0010 | [ding-dong] |
| 3_1-0015 | [jingle] |
| 3_1-0020 | [ding-dong] |
| 3_1-0022 | [ding-dong] |
| 3_1-0023 | I cannot read this book |

## Third firmware part, sounds from the second table, old firmware

| Third part, second table | Sound |
|---|---|
| 3-0013 | Calculator |
| 3-0014 – 3-0023 | Zero, One, Two, Three, Four, Five, Six, Seven, Eight, Nine |
| 3-0024 – 3-0027 | [Chinese] |
| 3-0028 | Plus |
| 3-0029 | Minus |
| 3-0030 | Times |
| 3-0031 | Divided by |
| 3-0032 | Equals |
| 3-0033 | [another ding-dong] |
| 3-0034 | The result is outside the calculator's number range |
| 3-0035 – 3-0038 | [Chinese] |
| 3-0039 | [click] |
| 3-0040 | [bim-bam] |
| 3-0041 | [bim-bam] |
| 3-0042 – 3-0067 | Spelled English alphabet |

Even after several thorough searches it looks like these sounds are no longer present in the new firmware
version at all.

## Third firmware part, texts from the third table, old firmware

| # | Text |
|---|---|
| 0 | `sd:\` |
| 1 | `sd:\` |
| 2 | `sd:\` |
| 3 | `sd:\Rec` |
| 4 | `sd:\` |
| 5 | `sd:\` |
| 6 | `bnl` |
| 7 | `mp3` |
| 8 | `tn2` |
| 9 | `wav` |
| 10 | `bmd` |
| 11 | `tn2` |

## First firmware part, texts, old firmware

Some are song titles, some are texts of old books and their chapter titles, old sayings.

The original lists each entry as: number, Chinese original, Czech translation (machine translated, only for
entries 0–115 and 200). The English titles below are translated from the Czech; where the Czech machine
translation clearly referred to a well-known piece, its usual English title is used.

| # | Title | # | Title |
|---|---|---|---|
| 0 | Dance No. 11 – Chopin | 58 | Puppy (Minute) Waltz – Chopin |
| 1 | Spring Song | 59 | Symphony No. 101 |
| 2 | Autumn Whispers | 60 | Pastoral Symphony |
| 3 | Snowflake Drift | 61 | Chinese Dance |
| 4 | Piano Sonata (Appassionata) | 62 | March in G♭ major – Schubert |
| 5 | Piano Sonata No. 4 | 63 | Fate |
| 6 | Liszt Serenade | 64 | Raindrop Prelude in D♭ major |
| 7 | Barcarolle – Tchaikovsky | 65 | Hungarian Dance from Swan Lake |
| 8 | Farewell piece | 66 | Piano Concerto No. 20 |
| 9 | Variations on "Twinkle, Twinkle, Little Star" | 67 | Piano Sonata No. 15 |
| 10 | Hungarian Dance No. 5 | 68 | Brandenburg Concerto in G major |
| 11 | Moonlight Sonata | 69 | Violin Concerto No. 5 – Mozart |
| 12 | A Child Goes to Sleep | 70 | Ballade pour Adeline |
| 13 | Dream of Love (piano version) | 71 | Dance of the Little Swans – Tchaikovsky |
| 14 | Puppy (Minute) Waltz – Chopin | 72 | Childhood Memories |
| 15 | March in G♭ major – Schubert | 73 | Turkish March |
| 16 | Raindrop Prelude in D♭ major | 74 | Ave Maria |
| 17 | Piano Sonata No. 15 | 75 | Chopin Serenade |
| 18 | Piano Concerto No. 1, 1st movement | 76 | Romance 6 |
| 19 | Fantaisie-Impromptu | 77 | Dream of Love |
| 20 | Canon in D major | 78 | Drdla Serenade |
| 21 | Souvenir of Love – Richard Clayderman | 79 | Serenade – Haydn |
| 22 | Impromptu | 80 | Fantaisie-Impromptu |
| 23 | Toccata – Bach | 81 | Angel's Serenade |
| 24 | Surprise Symphony | 82 | Humoresque |
| 25 | Sabre Dance | 83 | Moonlight (remix version) |
| 26 | A Maiden's Prayer | 84 | Serenade – Pierné |
| 27 | Rondo for violin in a major key | 85 | Serenade for Strings, 1st movement |
| 28 | Water Music Suite in F major | 86 | Toselli Serenade |
| 29 | Piano Concerto No. 1, 1st movement | 87 | Serenade for Strings in G major |
| 30 | Carmen Overture – Bizet | 88 | Serenade for Strings, 4th movement 5 |
| 31 | Méditation | 89 | Memorial |
| 32 | Waltz of the Flowers | 90 | Moonlight Sonata |
| 33 | Dance from a musical evening feast | 91 | Praise of the God of Nature |
| 34 | Bell Tune | 92 | Lullaby – Mozart |
| 35 | Piano Sonata No. 4 | 93 | Love Concerto |
| 36 | Mandolin Concerto | 94 | Spring |
| 37 | Symphony No. 40, 1st movement | 95 | Träumerei (Fantasia) |
| 38 | L'Arlésienne | 96 | Songs My Mother Taught Me |
| 39 | Trout Variations | 97 | Minuet in G major |
| 40 | Andante cantabile | 98 | Spring (Four Seasons), 1st movement |
| 41 | Smile Polka | 99 | Spanish Serenade – Bizet |
| 42 | Waltz No. 2 | 100 | Serenade for Strings, 2nd movement |
| 43 | Flute Concerto No. 2 | 101 | Brahms Serenade |
| 44 | Cossack folk dance | 102 | Scenes from Childhood |
| 45 | Mozart Serenade | 103 | A Child Falls Asleep |
| 46 | Adagio in E major for violin | 104 | Minuet |
| 47 | Symphony No. 9 in E minor | 105 | Clair de Lune – Debussy |
| 48 | Serenade in D major | 106 | Für Elise |
| 49 | Love Song | 107 | Joy of Love |
| 50 | Hallelujah | 108 | Lovely Flute |
| 51 | Clarinet Concerto in A major | 109 | Autumn Whispers |
| 52 | Suite No. 2 | 110 | Drigo Serenade |
| 53 | Symphony No. 1 – Tchaikovsky | 111 | Ode to Joy |
| 54 | Gavotte | 112 | Swan Lake |
| 55 | Overture | 113 | Blue Love |
| 56 | Clarinet Concerto | 114 | The Blue Danube |
| 57 | Dance of the Chicks | 115 | Sleeping Beauty |

The rest of the table (pages 13–77 of the original) is in Chinese without translation, except English titles
that are in the firmware as they are. Overview:

| Entries | Content |
|---|---|
| 116–199 | empty |
| 200–316 | Chinese children's songs (200 = "I love my kindergarten") |
| 317–371 | English nursery rhymes (e.g. "Hickory, Dickory, Dock!", "London Bridge", "Row Your Boat") |
| 372–732 | Chinese children's songs and rhymes, including Cantonese and patriotic songs |
| 733–803 | English children's songs (e.g. "Are You Sleeping", "Bingo", "Old MacDonald", "Wheels on the Bus", "Twinkle, Twinkle, Little Star") |
| 804–899 | empty |
| 900–1887 | Chinese funny short stories, encyclopedic "why" questions for children (dinosaurs, animals, nature), classical texts (e.g. the Three Character Classic), Tang poems |
| 1888–2099 | empty |
| 2100–3653 | Chinese texts: English-learning songs, stories, fables (Aesop), fairy tales (Grimm, Andersen, One Thousand and One Nights), "Journey to the West" chapters |

## Disclaimer

This is the output of an unofficial and non-commercial project which is in no way affiliated with the Albi
company. The Albi company is not the author of this content, does not participate in its development, does not
endorse it and bears no responsibility for it. All product names, trademarks and logos belong to their
respective owners and are used for identification purposes only.

The aim of this project is technical analysis and documentation for educational purposes. All findings are the
result of independent research of a purchased device and are in no way connected with the manufacturer or
distributor.
