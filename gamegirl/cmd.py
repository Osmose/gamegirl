#!/usr/bin/env python
"""
Execute a GameBoy ROM.

Usage: gamegirl FILENAME

Options:
  --help                  Show this screen.
  --version               Show version.
"""
import struct

from docopt import docopt

import gamegirl


class Rom(object):
    GBC_INCOMPATIBLE = 0
    GBC_COMPATIBLE = 0x80
    GBC_EXCLUSIVE = 0xc0

    DESTINATION_JAPAN = 0
    DESTINATION_OTHER = 1

    ROM_SIZES = {
        0x00: (256 * 1024 / 8, '256 KBit'),
        0x01: (512 * 1024 / 8, '512 KBit'),
        0x02: (1 * 1024 * 1024 / 8, '1 MBit'),
        0x03: (2 * 1024 * 1024 / 8, '2 MBit'),
        0x04: (4 * 1024 * 1024 / 8, '4 MBit'),
        0x05: (8 * 1024 * 1024 / 8, '8 MBit'),
        0x06: (16 * 1024 * 1024 / 8, '16 MBit'),
        0x07: (32 * 1024 * 1024 / 8, '32 MBit'),
    }

    def __init__(self, rom_data):
        self.rom_data = rom_data

        # Pull data from header.
        self.title = self.string(0x134, 11)
        self.start_address = self.short(0x102)
        self.game_code = self.string(0x13f, 4)
        self.gbc_compatible = self.ubyte(0x143)
        self.maker_code = self.string(0x144, 2)
        self.super_gameboy = bool(self.ubyte(0x146))
        self.rom_size = self.ROM_SIZES[self.ubyte(0x148)]
        self.destination = self.ubyte(0x14a)
        self.mask_rom_version = self.ubyte(0x14c)
        self.checksum = self.short(0x14e)

        # Run complement check on header data.
        complement_check_sum = sum(self.ubytes(0x134, 0x14d)) + 0x19
        self.passed_complement_check = (complement_check_sum + self.ubyte(0x14d)) & 0xFF == 0

    def unpack(self, format_string, address, length):
        return struct.unpack(format_string, self.rom_data[address:address + length])

    def string(self, address, length):
        return self.unpack('<{0}s'.format(length), address, length)[0]

    def short(self, address):
        return self.unpack('<h', address, 2)[0]

    def ubyte(self, address):
        return self.unpack('<B', address, 1)[0]

    def ubytes(self, start_address, end_address):
        count = end_address - start_address
        return self.unpack('<{0}B'.format(count), start_address, count)


def main():
    args = docopt(__doc__, version=gamegirl.__version__)
    with open(args['FILENAME'], 'rb') as f:
        rom = Rom(f.read())

    # Print some info about the game we're running.
    print 'Game: ' + rom.title
    print 'Start address: 0x{0:04x}'.format(rom.start_address)
    print 'Game code: ' + rom.game_code

    if rom.gbc_compatible == Rom.GBC_INCOMPATIBLE:
        print 'Gameboy Color: Incompatible'
    elif rom.gbc_compatible == Rom.GBC_COMPATIBLE:
        print 'Gameboy Color: Compatible'
    elif rom.gbc_compatible == Rom.GBC_EXCLUSIVE:
        print 'Gameboy Color: Exclusive'
    else:
        print 'Gameboy Color: Unknown'

    print 'Maker code: ' + rom.maker_code
    print 'Super Gameboy: ' + ('Yes' if rom.super_gameboy else 'No')
    print 'ROM Size: ' + rom.rom_size[1]
    print 'Destination: ' + ('Other' if rom.destination == Rom.DESTINATION_OTHER else 'Japan')
    print 'Mask ROM Version: {0}'.format(rom.mask_rom_version)
    print 'Complement check: ' + ('Passed' if rom.passed_complement_check else 'Failed')
    print 'Checksum: 0x{0:04x}'.format(rom.checksum)

if __name__ == 'main':
    main()
