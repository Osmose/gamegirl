from functools import partial


# get_ functions are passed into instruction functions to customize how
# they load a value that they're operating on. They return the value
# they've fetched and a debug string for when debugging output is
# enabled.
def get_immediate_byte(cpu):
    value = cpu.read_next_byte()
    return value, '0x{0:04x}'.format(value)


def get_immediate_short(cpu):
    value = cpu.read_next_short()
    return value, '0x{0:04x}'.format(value)


def get_register(register, cpu):
    return getattr(cpu, register), register


get_register_A = partial(get_register, 'A')
get_register_B = partial(get_register, 'B')
get_register_C = partial(get_register, 'C')
get_register_D = partial(get_register, 'D')
get_register_E = partial(get_register, 'E')
get_register_H = partial(get_register, 'H')
get_register_L = partial(get_register, 'L')
get_register_BC = partial(get_register, 'BC')
get_register_DE = partial(get_register, 'DE')
get_register_HL = partial(get_register, 'HL')
get_register_SP = partial(get_register, 'SP')


def get_indirect_byte(register, cpu):
    address = getattr(cpu, register)
    return cpu.memory.read_byte(address), '({0})'.format(register)


get_indirect_byte_HL = partial(get_indirect_byte, 'HL')


# Instruction functions actually do the work of an instruction as well
# as printing debug info if necessary.
def load_register(cycles, register, get_value, cpu):
    value, debug_value = get_value(cpu)
    setattr(cpu, register, value)
    cpu.cycle(cycles)

    return 'LD {0},{1}'.format(register, debug_value)


def load_indirect(cycles, register, get_value, cpu):
    address = getattr(cpu, register)
    value, debug_value = get_value(cpu)
    cpu.memory.write_byte(address, value)
    cpu.cycle(cycles)

    return 'LD ({0}),{1}'.format(register, debug_value)


def load_indirect_decrement(cycles, register, get_value, cpu):
    log = load_indirect(cycles, register, get_value, cpu)

    # Decrement register
    value = getattr(cpu, register)
    setattr(cpu, register, value - 2)

    return log.replace('LD', 'LDD')


def push_short(cycles, register, cpu):
    cpu.memory.write_short(cpu.SP, getattr(cpu, register))
    cpu.SP -= 2
    cpu.cycle(cycles)

    return 'PUSH ' + register


def xor(cycles, get_value, cpu):
    value, debug_value = get_value(cpu)
    cpu.A = cpu.A ^ value
    cpu.cycle(cycles)

    cpu.flag_Z = cpu.A == 0
    cpu.flag_N = 0
    cpu.flag_H = 0
    cpu.flag_CY = 0

    return 'XOR {0}'.format(debug_value)


def swap(value, cpu):
    result = (value >> 4) & (value << 4)
    cpu.flag_Z = result == 0
    cpu.flag_N = 0
    cpu.flag_H = 0
    cpu.flag_CY = 0
    return result


def swap_register(cycles, register, cpu):
    value = getattr(cpu, register)
    result = swap(value, cpu)
    setattr(cpu, register, result)
    cpu.cycle(cycles)

    return 'SWAP {0}'.format(register)


def swap_indirect(cycles, register, cpu):
    address = getattr(cpu, register)
    value = cpu.memory.read_byte(address)
    result = swap(value, cpu)
    cpu.memory.write_byte(address, result)
    cpu.cycle(cycles)

    return 'SWAP ({0})'.format(register)


def cb_dispatch(cpu):
    opcode = cpu.read_next_byte()
    try:
        return CB_OPCODES[opcode](cpu)
    except KeyError:
        raise ValueError('Invalid CB opcode: 0x{0:02x}'.format(opcode))


OPCODES = {
    0x06: partial(load_register, 8, 'B', get_immediate_byte),
    0x0e: partial(load_register, 8, 'C', get_immediate_byte),
    0x16: partial(load_register, 8, 'D', get_immediate_byte),
    0x1e: partial(load_register, 8, 'E', get_immediate_byte),
    0x26: partial(load_register, 8, 'H', get_immediate_byte),
    0x2e: partial(load_register, 8, 'L', get_immediate_byte),

    0x01: partial(load_register, 12, 'BC', get_immediate_short),
    0x11: partial(load_register, 12, 'DE', get_immediate_short),
    0x21: partial(load_register, 12, 'HL', get_immediate_short),
    0x31: partial(load_register, 12, 'SP', get_immediate_short),

    0xf5: partial(push_short, 16, 'AF'),
    0xc5: partial(push_short, 16, 'BC'),
    0xd5: partial(push_short, 16, 'DE'),
    0xe5: partial(push_short, 16, 'HL'),

    0xaf: partial(xor, 4, get_register_A),
    0xa8: partial(xor, 4, get_register_B),
    0xa9: partial(xor, 4, get_register_C),
    0xaa: partial(xor, 4, get_register_D),
    0xab: partial(xor, 4, get_register_E),
    0xac: partial(xor, 4, get_register_H),
    0xad: partial(xor, 4, get_register_L),
    0xae: partial(xor, 8, get_indirect_byte_HL),
    0xee: partial(xor, 8, get_immediate_byte),

    0x7f: partial(load_register, 4, 'A', get_register_A),
    0x78: partial(load_register, 4, 'A', get_register_B),
    0x79: partial(load_register, 4, 'A', get_register_C),
    0x7a: partial(load_register, 4, 'A', get_register_D),
    0x7b: partial(load_register, 4, 'A', get_register_E),
    0x7c: partial(load_register, 4, 'A', get_register_H),
    0x7d: partial(load_register, 4, 'A', get_register_L),
    0x7e: partial(load_register, 8, 'A', get_indirect_byte_HL),

    0x40: partial(load_register, 4, 'B', get_register_B),
    0x41: partial(load_register, 4, 'B', get_register_C),
    0x42: partial(load_register, 4, 'B', get_register_D),
    0x43: partial(load_register, 4, 'B', get_register_E),
    0x44: partial(load_register, 4, 'B', get_register_H),
    0x45: partial(load_register, 4, 'B', get_register_L),
    0x46: partial(load_register, 8, 'B', get_indirect_byte_HL),

    0x48: partial(load_register, 4, 'C', get_register_B),
    0x49: partial(load_register, 4, 'C', get_register_C),
    0x4a: partial(load_register, 4, 'C', get_register_D),
    0x4b: partial(load_register, 4, 'C', get_register_E),
    0x4c: partial(load_register, 4, 'C', get_register_H),
    0x4d: partial(load_register, 4, 'C', get_register_L),
    0x4e: partial(load_register, 8, 'C', get_indirect_byte_HL),

    0x50: partial(load_register, 4, 'D', get_register_B),
    0x51: partial(load_register, 4, 'D', get_register_C),
    0x52: partial(load_register, 4, 'D', get_register_D),
    0x53: partial(load_register, 4, 'D', get_register_E),
    0x54: partial(load_register, 4, 'D', get_register_H),
    0x55: partial(load_register, 4, 'D', get_register_L),
    0x56: partial(load_register, 8, 'D', get_indirect_byte_HL),

    0x58: partial(load_register, 4, 'E', get_register_B),
    0x59: partial(load_register, 4, 'E', get_register_C),
    0x5a: partial(load_register, 4, 'E', get_register_D),
    0x5b: partial(load_register, 4, 'E', get_register_E),
    0x5c: partial(load_register, 4, 'E', get_register_H),
    0x5d: partial(load_register, 4, 'E', get_register_L),
    0x5e: partial(load_register, 8, 'E', get_indirect_byte_HL),

    0x60: partial(load_register, 4, 'H', get_register_B),
    0x61: partial(load_register, 4, 'H', get_register_C),
    0x62: partial(load_register, 4, 'H', get_register_D),
    0x63: partial(load_register, 4, 'H', get_register_E),
    0x64: partial(load_register, 4, 'H', get_register_H),
    0x65: partial(load_register, 4, 'H', get_register_L),
    0x66: partial(load_register, 8, 'H', get_indirect_byte_HL),

    0x68: partial(load_register, 4, 'L', get_register_B),
    0x69: partial(load_register, 4, 'L', get_register_C),
    0x6a: partial(load_register, 4, 'L', get_register_D),
    0x6b: partial(load_register, 4, 'L', get_register_E),
    0x6c: partial(load_register, 4, 'L', get_register_H),
    0x6d: partial(load_register, 4, 'L', get_register_L),
    0x6e: partial(load_register, 8, 'L', get_indirect_byte_HL),

    0x70: partial(load_indirect, 8, 'HL', get_register_B),
    0x71: partial(load_indirect, 8, 'HL', get_register_C),
    0x72: partial(load_indirect, 8, 'HL', get_register_D),
    0x73: partial(load_indirect, 8, 'HL', get_register_E),
    0x74: partial(load_indirect, 8, 'HL', get_register_H),
    0x75: partial(load_indirect, 8, 'HL', get_register_L),
    0x36: partial(load_indirect, 12, 'HL', get_immediate_byte),

    0x32: partial(load_indirect_decrement, 8, 'HL', get_register_A),

    0xcb: cb_dispatch,
}


CB_OPCODES = {
    0x37: partial(swap_register, 8, 'A'),
    0x30: partial(swap_register, 8, 'B'),
    0x31: partial(swap_register, 8, 'C'),
    0x32: partial(swap_register, 8, 'D'),
    0x33: partial(swap_register, 8, 'E'),
    0x34: partial(swap_register, 8, 'H'),
    0x35: partial(swap_register, 8, 'L'),
    0x36: partial(swap_indirect, 16, 'HL'),
}
