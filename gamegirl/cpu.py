from gamegirl.opcodes import OPCODES


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


class Stack(object):
    def __init__(self, cpu):
        self.cpu = cpu

    def push_short(self, value):
        self.cpu.memory.write_short(self.cpu.SP - 2, value)
        self.cpu.SP -= 2

    def pop_short(self):
        value = self.cpu.memory.read_short(self.cpu.SP)
        self.cpu.SP += 2
        return value


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
        self.debug_string = ''
        self.debug_kwargs = {}
        self.debug_last_bytes = []

        self.memory = memory
        self.stack = Stack(self)
        self.instruction_count = 0
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
        return self.execute(opcode)

    def read_next_byte(self):
        value = self.memory.read_byte(self.PC)
        self.PC += 1
        self.debug_last_bytes.append(value)
        return value

    def read_next_short(self):
        byte1 = self.memory.read_byte(self.PC)
        byte2 = self.memory.read_byte(self.PC + 1)
        self.debug_last_bytes += [byte1, byte2]

        value = self.memory.read_short(self.PC)
        self.PC += 2
        return value

    def execute(self, opcode):
        instruction = OPCODES.get(opcode)
        if not instruction:
            raise Exception('Unknown opcode: ${0:02x}'.format(opcode))

        if self.debug:
            self.debug_string = 'UNKNOWN'
            self.debug_kwargs = {}

        instruction(cpu=self)
        self.instruction_count += 1

        if self.debug:
            debug_bytes = self.debug_last_bytes
            self.debug_last_bytes = []
            return self.debug_string.format(**self.debug_kwargs), debug_bytes

    def cycle(self, cycles):
        self.cycles += cycles
