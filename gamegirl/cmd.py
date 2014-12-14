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
from docopt import docopt

import gamegirl
from gamegirl.cpu import CPU
from gamegirl.memory import Memory, Ram, Rom


def main():
    args = docopt(__doc__, version=gamegirl.__version__)
    with open(args['FILENAME'], 'rb') as f:
        rom = Rom(f.read())

    with open(args['--bios'], 'rb') as f:
        bios = Ram(f.read())

    # Print some info about the game we're running.
    print 'Game: ' + rom.title
    print 'Start address: ${0:04x}'.format(rom.start_address)
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
    print 'Checksum: ${0:04x}'.format(rom.checksum)
    print '-------------------'

    memory = Memory(rom=rom, bios=bios)
    cpu = CPU(memory=memory, debug=args['--debug'])
    cpu.PC = 0

    while True:
        cpu.read_and_execute()

if __name__ == 'main':
    main()
