# albituzka
Reverse engineering of the Albi Kouzelné čtení ("Magic Reading") pen.

The docs directory contains a description of the BNL format and of the firmware contents.

The tools directory contains tools for disassembling and assembling BNL files, an OID code generator and other tools.

The test directory contains a sample file for a custom book together with its source materials.

Reverse engineering of BNL files used for Albi electronic pen. Works also for files found on SpeakItBooks.com. To check if this description is valid for your BNL files, XOR first two 32bit DWORDs, you should get 0x200 in little endian.


Disclaimer:
This is an _unofficial_ and _non-commercial_ project which is _in no way_ affiliated with the Albi company.

The Albi company is not the author of this content, does not participate in its development, does not endorse it and bears no responsibility for it. All product names, trademarks and logos belong to their respective owners and are used for identification purposes only.

The aim of this project is technical analysis and documentation for educational purposes. All findings are the result of independent research of a purchased device and are in no way connected with the manufacturer or distributor.
