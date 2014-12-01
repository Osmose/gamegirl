#!/usr/bin/env python
"""
Execute a GameBoy ROM.

Usage: gamegirl FILENAME [options]

Options:
  --help           Show this screen.
  --version        Show version.
  --bios FILENAME  Path to Gameboy BIOS ROM. [default: bios.gb]
  --debug          Output logging for debugging.
"""
import struct

from docopt import docopt

import gamegirl
from gamegirl.opcodes import OPCODES


class ReadableMemory(object):
    def unpack(self, format_string, address, length):
        return struct.unpack(format_string, self.raw_data[address:address + length])

    def read_string(self, address, length):
        return self.unpack('<{0}s'.format(length), address, length)[0]

    def read_short(self, address):
        return self.unpack('<H', address, 2)[0]

    def read_byte(self, address):
        return self.unpack('<B', address, 1)[0]

    def read_bytes(self, start_address, end_address):
        count = end_address - start_address
        return self.unpack('<{0}B'.format(count), start_address, count)


class WriteableMemory(object):
    def pack_into(self, format_string, address, *values):
        struct.pack_into(format_string, self.raw_data, address, *values)

    def write_short(self, address, value):
        return self.pack_into('<H', address, value)

    def write_byte(self, address, value):
        return self.pack_into('<B', address, value)


class Rom(ReadableMemory):
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
        self.title = self.read_string(0x134, 11)
        self.start_address = self.read_short(0x102)
        self.game_code = self.read_string(0x13f, 4)
        self.gbc_compatible = self.read_byte(0x143)
        self.maker_code = self.read_string(0x144, 2)
        self.super_gameboy = bool(self.read_byte(0x146))
        self.rom_size = self.ROM_SIZES[self.read_byte(0x148)]
        self.destination = self.read_byte(0x14a)
        self.mask_rom_version = self.read_byte(0x14c)
        self.checksum = self.read_short(0x14e)

        # Run complement check on header data.
        complement_check_sum = sum(self.read_bytes(0x134, 0x14d)) + 0x19
        self.passed_complement_check = (complement_check_sum + self.read_byte(0x14d)) & 0xFF == 0

    @property
    def raw_data(self):
        return self.rom_data


class Ram(ReadableMemory, WriteableMemory):
    def __init__(self, size):
        self.raw_data = bytearray(size)


class Memory(object):
    def __init__(self, rom, bios):
        self.rom = rom
        self.bios = bios
        self.bios_enabled = True

        self.wram = Ram(8 * 1024)
        self.stack = Ram(127)
        self.lcd_ram = Ram(8 * 1024)

    def read_string(self, address, length):
        memory, offset = self._get_memory(address, address + length)
        return memory.read_string(address - offset, length)

    def read_short(self, address):
        memory, offset = self._get_memory(address, address + 2)
        return memory.read_short(address - offset)

    def write_short(self, address, value):
        memory, offset = self._get_memory(address, address + 2)
        memory.write_short(address - offset, value)

    def read_byte(self, address):
        memory, offset = self._get_memory(address, address + 1)
        return memory.read_byte(address - offset)

    def write_byte(self, address, value):
        memory, offset = self._get_memory(address, address + 1)
        return memory.write_byte(address - offset, value)

    def read_bytes(self, start_address, end_address):
        memory, offset = self._get_memory(start_address, end_address)
        return memory.read_bytes(start_address - offset, end_address - offset)

    def _get_memory(self, start_address, end_address):
        # Special case: While the bios is enabled, it replaces the first
        # 256 bytes of memory.
        if start_address < end_address <= 0xFF and self.bios_enabled:
            return self.bios, 0

        # Game cart ROM
        if start_address < end_address <= 0x8000:
            return self.rom, 0

        # LCD RAM
        if 0x8000 <= start_address < end_address <= 0xa000:
            return self.lcd_ram, 0x8000

        # Working RAM
        if 0xc000 <= start_address < end_address <= 0xe000:
            return self.wram, 0xc000

        # Mirror of Working RAM
        if 0xe000 <= start_address < end_address <= 0xfe00:
            return self.wram, 0xe000

        # Stack RAM
        if 0xff80 <= start_address < end_address <= 0xfffe:
            return self.stack, 0xff80

        raise ValueError('Invalid memory range: {0:04x} - {1:04x}'
                         .format(start_address, end_address))


def register_pair(hi, lo):
    def getter(self):
        return (getattr(self, hi) << 8) | getattr(self, lo)

    def setter(self, value):
        setattr(self, hi, (value >> 8) & 0xff)
        setattr(self, lo, value & 0xff)

    return property(getter, setter)


def flag(bit):
    def getter(self):
        return (self.F >> bit) & 0x1

    def setter(self, value):
        self.F = self.F | (value << bit)

    return property(getter, setter)


class CPU(object):
    BYTE_REGISTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'H', 'L']
    SHORT_REGISTERS = ['PC', 'SP']

    AF = register_pair('A', 'F')
    BC = register_pair('B', 'C')
    DE = register_pair('D', 'E')
    HL = register_pair('H', 'L')

    flag_Z = flag(7)
    flag_N = flag(6)
    flag_H = flag(5)
    flag_C = flag(4)

    def __init__(self, memory, debug=False):
        self.debug = debug

        self.memory = memory
        self.cycles = 0

        self.A = 0
        self.B = 0
        self.C = 0
        self.D = 0
        self.E = 0
        self.F = 0
        self.H = 0
        self.L = 0
        self.PC = 0
        self.SP = 0

    def __setattr__(self, name, value):
        # Keep registers limited to the right size.
        if name in self.BYTE_REGISTERS:
            value = value & 0xff
        elif name in self.SHORT_REGISTERS:
            value = value & 0xffff

        return super(CPU, self).__setattr__(name, value)

    def read_and_execute(self):
        opcode = self.read_next_byte()
        self.execute(opcode)

    def read_next_byte(self):
        value = self.memory.read_byte(self.PC)
        self.PC += 1
        return value

    def read_next_short(self):
        value = self.memory.read_short(self.PC)
        self.PC += 2
        return value

    def execute(self, opcode):
        instruction = OPCODES.get(opcode)
        if not instruction:
            raise Exception('Unknown opcode: 0x{0:02x}'.format(opcode))

        log = instruction(self)
        if self.debug:
            print log

    def cycle(self, cycles):
        self.cycles += cycles


def main():
    args = docopt(__doc__, version=gamegirl.__version__)
    with open(args['FILENAME'], 'rb') as f:
        rom = Rom(f.read())

    with open(args['--bios'], 'rb') as f:
        bios = Ram(f.read())

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
    print '-------------------'

    memory = Memory(rom=rom, bios=bios)
    cpu = CPU(memory=memory, debug=args['--debug'])
    cpu.PC = 0

    while True:
        cpu.read_and_execute()

if __name__ == 'main':
    main()
