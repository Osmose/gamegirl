from functools import partial


def load_immediate(register, cpu):
    value = cpu.next_ubyte()
    setattr(cpu, register, value)
    cpu.cycle(8)


OPCODES = {
    0x06: partial(load_immediate, 'B'),
    0x0E: partial(load_immediate, 'C'),
    0x16: partial(load_immediate, 'D'),
    0x1E: partial(load_immediate, 'E'),
    0x26: partial(load_immediate, 'H'),
    0x2E: partial(load_immediate, 'L'),
}
