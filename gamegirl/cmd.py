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
from gamegirl.debugger import DebuggerInterface
from gamegirl.memory import Memory, Ram, Rom


def main():
    args = docopt(__doc__, version=gamegirl.__version__)
    with open(args['FILENAME'], 'rb') as f:
        rom = Rom(f.read())

    with open(args['--bios'], 'rb') as f:
        bios = Ram(f.read())

    debug = args['--debug']
    memory = Memory(rom=rom, bios=bios)
    cpu = CPU(memory=memory, debug=debug)
    cpu.PC = 0

    if debug:
        interface = DebuggerInterface(cpu)
        interface.start()
    else:
        while True:
            cpu.read_and_execute()

if __name__ == 'main':
    main()
