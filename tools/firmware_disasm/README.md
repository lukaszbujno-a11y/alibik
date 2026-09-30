
These are tools for creating a disassembled firmware with the help of a semi-automatic disassembler.
The disassembler code itself comes from this repository: https://github.com/marian-m12l/s9ke-toolchain but it now makes up at most half
of this program - an instruction mutator, symbol support (including automatic symbols), cross-references etc. were added. The input for dissector.py is a hand-written
'description' of the firmware, which tells the disassembler how to walk through the individual firmware blocks one by one - it deals only with the 1.bin part, which contains the actual code,
however the code shows dependencies on the other parts.

dissector.py - disassembler

mapfile_old.def - contains the description of the second oldest firmware (this file will no longer be updated)

mapfile.def - contains the description of the newest firmware

rom_dumper.asm - code for dumping the ROM from the Sonix DSP
