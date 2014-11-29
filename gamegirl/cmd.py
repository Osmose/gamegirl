#!/usr/bin/env python
"""
Execute a GameBoy ROM.

Usage: gamegirl FILENAME

Options:
  --help                  Show this screen.
  --version               Show version.
"""
import struct
from ctypes import c_ubyte, c_ushort

from docopt import docopt

import gamegirl
from gamegirl.opcodes import OPCODES


class ReadableMemory(object):
    def unpack(self, format_string, address, length):
        return struct.unpack(format_string, self.raw_data[address:address + length])

    def string(self, address, length):
        return self.unpack('<{0}s'.format(length), address, length)[0]

    def short(self, address):
        return self.unpack('<h', address, 2)[0]

    def ubyte(self, address):
        return self.unpack('<B', address, 1)[0]

    def ubytes(self, start_address, end_address):
        count = end_address - start_address
        return self.unpack('<{0}B'.format(count), start_address, count)


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

    @property
    def raw_data(self):
        return self.rom_data


class Ram(ReadableMemory):
    def __init__(self, size):
        self.raw_data = bytearray(size)


class Memory(object):
    def __init__(self, rom):
        self.rom = rom

        self.working_ram = Ram(8 * 1024)
        self.stack = Ram(127)

    def string(self, address, length):
        memory, offset = self._get_memory(address, address + length)
        memory.string(address - offset, length)

    def short(self, address):
        memory, offset = self._get_memory(address, address + 2)
        return memory.short(address - offset)

    def ubyte(self, address):
        memory, offset = self._get_memory(address, address + 1)
        return memory.ubyte(address - offset)

    def ubytes(self, start_address, end_address):
        memory, offset = self._get_memory(start_address, end_address)
        return memory.ubytes(start_address - offset, end_address - offset)

    def _get_memory(self, start_address, end_address):
        if start_address < end_address <= 0x8000:
            return self.rom, 0
        elif 0xc000 <= start_address < end_address < 0xe000:
            return self.working_ram, 0xc000
        elif 0xe000 <= start_address < end_address < 0xfe00:  # Mirror
            return self.working_ram, 0xe000
        elif 0xff80 <= start_address < end_address < 0xfffe:
            return self.stack, 0xff80
        else:
            raise ValueError('Invalid memory range: {0:04x} - {1:04x}'
                             .format(start_address, end_address))


class CPU(object):
    BYTE_REGISTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'H', 'L']
    SHORT_REGISTERS = ['PC', 'SP']

    def __init__(self, memory):
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
        opcode = self.next_ubyte()
        self.execute(opcode)

    def next_ubyte(self):
        value = self.memory.ubyte(self.PC)
        self.PC += 1
        return value

    def execute(self, opcode):
        instruction = OPCODES.get(opcode)
        if not instruction:
            raise Exception('Unknown opcode: 0x{0:02x}'.format(opcode))

        instruction(self)

    def cycle(self, cycles):
        self.cycles += cycles


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

    memory = Memory(rom=rom)
    cpu = CPU(memory=memory)
    cpu.PC = rom.start_address

    while True:
        cpu.read_and_execute()

if __name__ == 'main':
    main()
