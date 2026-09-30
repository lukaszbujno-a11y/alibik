
### Environment
All tools were written under Windows 10, on ActiveState Perl 5.24.3. In theory, no modifications should be needed to run them
on another OS. You may need to install some modules which are not a typical part of the installation,
e.g. Imager, Imager::Fill, YAML, MP3::Info and others. How to install modules can be found in the documentation.
A test was also done on Windows 7 with Strawberry Perl, everything works. The first attempt at documenting the scripts can be found in docs/albituzka_nastroje.pdf
All tools are command-line only, they have no graphical interface.

### Description of the tools in this directory
For how the tools work together when creating a book, see [docs/creating_a_book.md](../docs/creating_a_book.md).

creator/bnl_creator.pl - generates a BNL file from many mp3 files and bnl.yaml. These can be obtained with bnl_dis.pl from an existing bnl file

disassembler/bnl_dis.pl - disassembles a BNL file into mp3 files and bnl.yaml.

firmware_cutter/fw_cutter.pl - identifies and cuts up the contents of the update.chp firmware file

firmware_disasm - tool for disassembling the firmware

oid_generator/oid_png_generator - generates a printable png file with one OID code, or more from an input file

oid_rawtable/oid_table_extract - extracts the conversion table of OID 2.0 raw codes to internal codes from the OidCreator tool

