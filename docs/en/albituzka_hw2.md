# Albi pen 2.0 – hardware analysis

English translation of [albituzka_hw2.pdf](../albituzka_hw2.pdf) (Czech original). The photos are only in the
original PDF.
https://github.com/jindroush/albituzka

## Albi pen 2.0 – description of parts

Legend of the manufacturer's picture on page 1 of the original:

1. Power on/off button, playing an MP3 file
2. Pen reset hole
3. LED indicator (charging, low battery, searching for and connecting Bluetooth devices)
4. USB-C charging port
5. Closed memory card slot
6. Volume up / next MP3 track
7. Pen LED backlight (pen running indicator)
8. Optical sensor
9. Volume down / previous MP3 track
10. 3.5 mm jack socket (headphones or speaker)
11. Repeat / Bluetooth activation button
12. Speaker
13. Lanyard hole

The picture also says "16 GB memory", "Bluetooth" and "MP3 player".

## Description

Albi started selling the new Albi pen 2.0 (marked with serial number R50) sometime around May/June 2022.
The hardware description matches, except that some sources say a 16 GB or 32 GB card is inside; I only found
an 8 GB one.

*Photo: top side of the board.*

*Photo: bottom side of the board. The wires lead to the battery and the speaker.*

*Photo: the sensor module itself, with illumination, reading and evaluation of the result.*

## Components

| Designator | Component | Description |
|---|---|---|
| U1 | Winbond 25Q32JVS10 | Serial flash, 32 Mbit |
| U2 | Sonix SNAP01A | Mono speaker amplifier |
| U3 | Sonix SN9503FG | 16-bit DSP, the brain of the system |
| U4 | JL (JieLi) AC21BE00716-5A8 | Bluetooth, most likely identical to AC6905A |
| U5 | 65b136 | Li-Ion battery protection/charging. Almost certainly TP4065. |
| U6 | Microne S2UE, SOT-23-5 package | 3.3 V regulator, ME6211 |
| U7 | FT24C02A | Serial EEPROM, 2 kbit (datasheet can be found by manufacturer) |
| K1 | Button | Power |
| K2 | Button | Vol + |
| K3 | Button | Repeat |
| K4 | Button | Vol − |
| K9 | Button | ? hidden ? |
| J1 | Connection | Unknown, test? |
| J2 | Connector | 3.5 mm jack |
| J4 | Connection | For the OID module |
| Connected to J4 | Most likely Sonix SNM9S102C3000A | OID reader module |
| E1 | ? | SMD Bluetooth antenna |
| Y1 | H241K | Crystal for the BT chip, probably 24 MHz |
| Y2 | H121G | Probably 12 MHz crystal for the DSP |

The original links a datasheet for most components.

## Disclaimer

This is an unofficial and non-commercial project which is in no way affiliated with the Albi company.
The Albi company is not the author of this content, does not participate in its development, does not endorse
it and bears no responsibility for it. All product names, trademarks and logos belong to their respective
owners and are used for identification purposes only.

The aim of this project is technical analysis and documentation for educational purposes. All findings are
the result of independent research of a purchased device and are in no way connected with the manufacturer
or distributor.
