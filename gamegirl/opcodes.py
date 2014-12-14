from functools import partial


## Reading Values ######################################################

def get_immediate_byte(cpu):
    value = cpu.read_next_byte()
    return value, '${0:04x}'.format(value)


def get_immediate_short(cpu):
    value = cpu.read_next_short()
    return value, '${0:04x}'.format(value)


def get_register(cpu, register):
    return getattr(cpu, register), register


get_register_A = partial(get_register, register='A')
get_register_B = partial(get_register, register='B')
get_register_C = partial(get_register, register='C')
get_register_D = partial(get_register, register='D')
get_register_E = partial(get_register, register='E')
get_register_H = partial(get_register, register='H')
get_register_L = partial(get_register, register='L')
get_register_AF = partial(get_register, register='AF')
get_register_BC = partial(get_register, register='BC')
get_register_DE = partial(get_register, register='DE')
get_register_HL = partial(get_register, register='HL')
get_register_SP = partial(get_register, register='SP')


def get_indirect_register(cpu, register):
    address = getattr(cpu, register)
    value = cpu.memory.read_byte(address)
    return value, '({0})'.format(register)


def get_indirect_byte(cpu, register):
    address = getattr(cpu, register)
    return cpu.memory.read_byte(address), '({0})'.format(register)


get_indirect_byte_HL = partial(get_indirect_byte, 'HL')
get_indirect_byte_BC = partial(get_indirect_byte, 'BC')
get_indirect_byte_DE = partial(get_indirect_byte, 'DE')


def get_indirect_byte_immediate(cpu):
    address = cpu.read_next_short()
    return cpu.memory.read_byte(address), '(${0:04x})'.format(address)


## Writing Values ######################################################

def write_register(cpu, register, value):
    setattr(cpu, register, value)
    return register


write_register_A = partial(write_register, register='A')
write_register_B = partial(write_register, register='B')
write_register_C = partial(write_register, register='C')
write_register_D = partial(write_register, register='D')
write_register_E = partial(write_register, register='E')
write_register_H = partial(write_register, register='H')
write_register_L = partial(write_register, register='L')
write_register_BC = partial(write_register, register='BC')
write_register_DE = partial(write_register, register='DE')
write_register_HL = partial(write_register, register='HL')
write_register_SP = partial(write_register, register='SP')


def write_indirect_byte(cpu, register, value):
    address = getattr(cpu, register)
    cpu.memory.write_byte(address, value)
    return '({0})'.format(register)


write_indirect_byte_HL = partial(write_indirect_byte, register='HL')


def write_indirect_offset_byte(cpu, register, value):
    address = 0xff00 + getattr(cpu, register)
    cpu.memory.write_byte(address, value)
    return '($ff00+{0})'.format(register)


write_indirect_offset_byte_C = partial(write_indirect_offset_byte, register='C')


def write_indirect_decrement(cpu, register, value):
    address = getattr(cpu, register)
    cpu.memory.write_byte(address, value)
    setattr(cpu, register, address - 1)
    return '({0}-)'.format(register)


write_indirect_decrement_HL = partial(write_indirect_decrement, register='HL')


## Checking Flags ######################################################

def is_flag_set(flag, cpu):
    return bool(getattr(cpu, 'flag_' + flag)), flag


is_flag_Z_set = partial(is_flag_set, 'Z')
is_flag_N_set = partial(is_flag_set, 'N')
is_flag_H_set = partial(is_flag_set, 'H')
is_flag_C_set = partial(is_flag_set, 'C')


def is_flag_reset(flag, cpu):
    is_set, log_operand = is_flag_set(flag, cpu)
    return not is_set, 'N' + log_operand


is_flag_Z_reset = partial(is_flag_reset, 'Z')
is_flag_N_reset = partial(is_flag_reset, 'N')
is_flag_H_reset = partial(is_flag_reset, 'H')
is_flag_C_reset = partial(is_flag_reset, 'C')


## Instructions ########################################################

def load(cpu, get, write, cycles):
    value, debug_value = get(cpu=cpu)
    debug_destination = write(cpu=cpu, value=value)

    cpu.cycle(cycles)
    return 'LD {0},{1}'.format(debug_destination, debug_value)


def push_short(cpu, get, cycles):
    value, debug_value = get(cpu=cpu)
    cpu.memory.write_short(cpu.SP, value)
    cpu.SP -= 2

    cpu.cycle(cycles)
    return 'PUSH ' + debug_value


def xor(cpu, get, cycles):
    value, debug_value = get(cpu=cpu)
    cpu.A = cpu.A ^ value

    cpu.flag_Z = cpu.A == 0
    cpu.flag_N = 0
    cpu.flag_H = 0
    cpu.flag_C = 0

    cpu.cycle(cycles)
    return 'XOR ' + debug_value


def swap(cpu, get, write, cycles):
    value, debug_value = get(cpu=cpu)
    result = (value >> 4) & (value << 4)
    write(cpu=cpu, value=result)

    cpu.flag_Z = result == 0
    cpu.flag_N = 0
    cpu.flag_H = 0
    cpu.flag_C = 0

    cpu.cycle(cycles)
    return 'SWAP ' + debug_value


def jump_condition(cpu, get, condition, cycles):
    value, _ = get(cpu=cpu)
    result, log_operand = condition(cpu=cpu)
    if result:
        cpu.PC += value

    cpu.cycle(cycles)
    return 'JR {0},${1:02x}'.format(log_operand, value)


def cb_dispatch(cpu):
    opcode = cpu.read_next_byte()
    try:
        return CB_OPCODES[opcode](cpu=cpu)
    except KeyError:
        raise ValueError('Invalid CB opcode: ${0:02x}'.format(opcode))


def bit(cpu, get, bit, cycles):
    value, debug_value = get(cpu=cpu)
    result = (value >> bit) & 0x1
    cpu.flag_Z = result == 0
    cpu.flag_N = 0
    cpu.flag_H = 1

    cpu.cycle(cycles)
    return 'BIT {0},{1}'.format(bit, debug_value)


## Jump Tables #########################################################

OPCODES = {
    0x06: partial(load, cycles=8, get=get_immediate_byte, write=write_register_B),
    0x0e: partial(load, cycles=8, get=get_immediate_byte, write=write_register_C),
    0x16: partial(load, cycles=8, get=get_immediate_byte, write=write_register_D),
    0x1e: partial(load, cycles=8, get=get_immediate_byte, write=write_register_E),
    0x26: partial(load, cycles=8, get=get_immediate_byte, write=write_register_H),
    0x2e: partial(load, cycles=8, get=get_immediate_byte, write=write_register_L),

    0x01: partial(load, cycles=12, get=get_immediate_short, write=write_register_BC),
    0x11: partial(load, cycles=12, get=get_immediate_short, write=write_register_DE),
    0x21: partial(load, cycles=12, get=get_immediate_short, write=write_register_HL),
    0x31: partial(load, cycles=12, get=get_immediate_short, write=write_register_SP),

    0xf5: partial(push_short, cycles=16, get=get_register_AF),
    0xc5: partial(push_short, cycles=16, get=get_register_BC),
    0xd5: partial(push_short, cycles=16, get=get_register_DE),
    0xe5: partial(push_short, cycles=16, get=get_register_HL),

    0xaf: partial(xor, cycles=4, get=get_register_A),
    0xa8: partial(xor, cycles=4, get=get_register_B),
    0xa9: partial(xor, cycles=4, get=get_register_C),
    0xaa: partial(xor, cycles=4, get=get_register_D),
    0xab: partial(xor, cycles=4, get=get_register_E),
    0xac: partial(xor, cycles=4, get=get_register_H),
    0xad: partial(xor, cycles=4, get=get_register_L),
    0xae: partial(xor, cycles=8, get=get_indirect_byte_HL),
    0xee: partial(xor, cycles=8, get=get_immediate_byte),

    0x7f: partial(load, cycles=4, get=get_register_A, write=write_register_A),
    0x78: partial(load, cycles=4, get=get_register_B, write=write_register_A),
    0x79: partial(load, cycles=4, get=get_register_C, write=write_register_A),
    0x7a: partial(load, cycles=4, get=get_register_D, write=write_register_A),
    0x7b: partial(load, cycles=4, get=get_register_E, write=write_register_A),
    0x7c: partial(load, cycles=4, get=get_register_H, write=write_register_A),
    0x7d: partial(load, cycles=4, get=get_register_L, write=write_register_A),
    0x7e: partial(load, cycles=8, get=get_indirect_byte_HL, write=write_register_A),

    0x0a: partial(load, cycles=8, get=get_indirect_byte_BC, write=write_register_A),
    0x1a: partial(load, cycles=8, get=get_indirect_byte_DE, write=write_register_A),
    0x7e: partial(load, cycles=8, get=get_indirect_byte_HL, write=write_register_A),
    0xfa: partial(load, cycles=16, get=get_indirect_byte_immediate, write=write_register_A),
    0x3e: partial(load, cycles=8, get=get_immediate_byte, write=write_register_A),

    0x40: partial(load, cycles=4, get=get_register_B, write=write_register_B),
    0x41: partial(load, cycles=4, get=get_register_C, write=write_register_B),
    0x42: partial(load, cycles=4, get=get_register_D, write=write_register_B),
    0x43: partial(load, cycles=4, get=get_register_E, write=write_register_B),
    0x44: partial(load, cycles=4, get=get_register_H, write=write_register_B),
    0x45: partial(load, cycles=4, get=get_register_L, write=write_register_B),
    0x46: partial(load, cycles=8, get=get_indirect_byte_HL, write=write_register_B),

    0x48: partial(load, cycles=4, get=get_register_B, write=write_register_C),
    0x49: partial(load, cycles=4, get=get_register_C, write=write_register_C),
    0x4a: partial(load, cycles=4, get=get_register_D, write=write_register_C),
    0x4b: partial(load, cycles=4, get=get_register_E, write=write_register_C),
    0x4c: partial(load, cycles=4, get=get_register_H, write=write_register_C),
    0x4d: partial(load, cycles=4, get=get_register_L, write=write_register_C),
    0x4e: partial(load, cycles=8, get=get_indirect_byte_HL, write=write_register_C),

    0x50: partial(load, cycles=4, get=get_register_B, write=write_register_D),
    0x51: partial(load, cycles=4, get=get_register_C, write=write_register_D),
    0x52: partial(load, cycles=4, get=get_register_D, write=write_register_D),
    0x53: partial(load, cycles=4, get=get_register_E, write=write_register_D),
    0x54: partial(load, cycles=4, get=get_register_H, write=write_register_D),
    0x55: partial(load, cycles=4, get=get_register_L, write=write_register_D),
    0x56: partial(load, cycles=8, get=get_indirect_byte_HL, write=write_register_D),

    0x58: partial(load, cycles=4, get=get_register_B, write=write_register_E),
    0x59: partial(load, cycles=4, get=get_register_C, write=write_register_E),
    0x5a: partial(load, cycles=4, get=get_register_D, write=write_register_E),
    0x5b: partial(load, cycles=4, get=get_register_E, write=write_register_E),
    0x5c: partial(load, cycles=4, get=get_register_H, write=write_register_E),
    0x5d: partial(load, cycles=4, get=get_register_L, write=write_register_E),
    0x5e: partial(load, cycles=8, get=get_indirect_byte_HL, write=write_register_E),

    0x60: partial(load, cycles=4, get=get_register_B, write=write_register_H),
    0x61: partial(load, cycles=4, get=get_register_C, write=write_register_H),
    0x62: partial(load, cycles=4, get=get_register_D, write=write_register_H),
    0x63: partial(load, cycles=4, get=get_register_E, write=write_register_H),
    0x64: partial(load, cycles=4, get=get_register_H, write=write_register_H),
    0x65: partial(load, cycles=4, get=get_register_L, write=write_register_H),
    0x66: partial(load, cycles=8, get=get_indirect_byte_HL, write=write_register_H),

    0x68: partial(load, cycles=4, get=get_register_B, write=write_register_L),
    0x69: partial(load, cycles=4, get=get_register_C, write=write_register_L),
    0x6a: partial(load, cycles=4, get=get_register_D, write=write_register_L),
    0x6b: partial(load, cycles=4, get=get_register_E, write=write_register_L),
    0x6c: partial(load, cycles=4, get=get_register_H, write=write_register_L),
    0x6d: partial(load, cycles=4, get=get_register_L, write=write_register_L),
    0x6e: partial(load, cycles=8, get=get_indirect_byte_HL, write=write_register_L),

    0x70: partial(load, cycles=8, get=get_register_B, write=write_indirect_byte_HL),
    0x71: partial(load, cycles=8, get=get_register_C, write=write_indirect_byte_HL),
    0x72: partial(load, cycles=8, get=get_register_D, write=write_indirect_byte_HL),
    0x73: partial(load, cycles=8, get=get_register_E, write=write_indirect_byte_HL),
    0x74: partial(load, cycles=8, get=get_register_H, write=write_indirect_byte_HL),
    0x75: partial(load, cycles=8, get=get_register_L, write=write_indirect_byte_HL),
    0x36: partial(load, cycles=12, get=get_immediate_byte, write=write_indirect_byte_HL),

    0x32: partial(load, cycles=8, get=get_register_A, write=write_indirect_decrement_HL),
    0xe2: partial(load, cycles=8, get=get_register_A, write=write_indirect_offset_byte_C),

    0xcb: cb_dispatch,

    0x20: partial(jump_condition, cycles=8, get=get_immediate_byte, condition=is_flag_Z_reset),
    0x28: partial(jump_condition, cycles=8, get=get_immediate_byte, condition=is_flag_Z_set),
    0x30: partial(jump_condition, cycles=8, get=get_immediate_byte, condition=is_flag_C_reset),
    0x38: partial(jump_condition, cycles=8, get=get_immediate_byte, condition=is_flag_C_set),
}


CB_OPCODES = {
    0x37: partial(swap, cycles=8, get=get_register_A, write=write_register_A),
    0x30: partial(swap, cycles=8, get=get_register_B, write=write_register_B),
    0x31: partial(swap, cycles=8, get=get_register_C, write=write_register_C),
    0x32: partial(swap, cycles=8, get=get_register_D, write=write_register_D),
    0x33: partial(swap, cycles=8, get=get_register_E, write=write_register_E),
    0x34: partial(swap, cycles=8, get=get_register_H, write=write_register_H),
    0x35: partial(swap, cycles=8, get=get_register_L, write=write_register_L),
    0x36: partial(swap, cycles=16, get=get_indirect_byte_HL, write=write_indirect_byte_HL),

    0x40: partial(bit, cycles=8, get=get_register_B, bit=0),
    0x41: partial(bit, cycles=8, get=get_register_C, bit=0),
    0x42: partial(bit, cycles=8, get=get_register_D, bit=0),
    0x43: partial(bit, cycles=8, get=get_register_E, bit=0),
    0x44: partial(bit, cycles=8, get=get_register_H, bit=0),
    0x45: partial(bit, cycles=8, get=get_register_L, bit=0),
    0x46: partial(bit, cycles=16, get=get_indirect_byte_HL, bit=0),
    0x47: partial(bit, cycles=8, get=get_register_A, bit=0),

    0x48: partial(bit, cycles=8, get=get_register_B, bit=1),
    0x49: partial(bit, cycles=8, get=get_register_C, bit=1),
    0x4a: partial(bit, cycles=8, get=get_register_D, bit=1),
    0x4b: partial(bit, cycles=8, get=get_register_E, bit=1),
    0x4c: partial(bit, cycles=8, get=get_register_H, bit=1),
    0x4d: partial(bit, cycles=8, get=get_register_L, bit=1),
    0x4e: partial(bit, cycles=16, get=get_indirect_byte_HL, bit=1),
    0x4f: partial(bit, cycles=8, get=get_register_A, bit=1),

    0x50: partial(bit, cycles=8, get=get_register_B, bit=2),
    0x51: partial(bit, cycles=8, get=get_register_C, bit=2),
    0x52: partial(bit, cycles=8, get=get_register_D, bit=2),
    0x53: partial(bit, cycles=8, get=get_register_E, bit=2),
    0x54: partial(bit, cycles=8, get=get_register_H, bit=2),
    0x55: partial(bit, cycles=8, get=get_register_L, bit=2),
    0x56: partial(bit, cycles=16, get=get_indirect_byte_HL, bit=2),
    0x57: partial(bit, cycles=8, get=get_register_A, bit=2),

    0x58: partial(bit, cycles=8, get=get_register_B, bit=3),
    0x59: partial(bit, cycles=8, get=get_register_C, bit=3),
    0x5a: partial(bit, cycles=8, get=get_register_D, bit=3),
    0x5b: partial(bit, cycles=8, get=get_register_E, bit=3),
    0x5c: partial(bit, cycles=8, get=get_register_H, bit=3),
    0x5d: partial(bit, cycles=8, get=get_register_L, bit=3),
    0x5e: partial(bit, cycles=16, get=get_indirect_byte_HL, bit=3),
    0x5f: partial(bit, cycles=8, get=get_register_A, bit=3),

    0x60: partial(bit, cycles=8, get=get_register_B, bit=4),
    0x61: partial(bit, cycles=8, get=get_register_C, bit=4),
    0x62: partial(bit, cycles=8, get=get_register_D, bit=4),
    0x63: partial(bit, cycles=8, get=get_register_E, bit=4),
    0x64: partial(bit, cycles=8, get=get_register_H, bit=4),
    0x65: partial(bit, cycles=8, get=get_register_L, bit=4),
    0x66: partial(bit, cycles=16, get=get_indirect_byte_HL, bit=4),
    0x67: partial(bit, cycles=8, get=get_register_A, bit=4),

    0x68: partial(bit, cycles=8, get=get_register_B, bit=5),
    0x69: partial(bit, cycles=8, get=get_register_C, bit=5),
    0x6a: partial(bit, cycles=8, get=get_register_D, bit=5),
    0x6b: partial(bit, cycles=8, get=get_register_E, bit=5),
    0x6c: partial(bit, cycles=8, get=get_register_H, bit=5),
    0x6d: partial(bit, cycles=8, get=get_register_L, bit=5),
    0x6e: partial(bit, cycles=16, get=get_indirect_byte_HL, bit=5),
    0x6f: partial(bit, cycles=8, get=get_register_A, bit=5),

    0x70: partial(bit, cycles=8, get=get_register_B, bit=6),
    0x71: partial(bit, cycles=8, get=get_register_C, bit=6),
    0x72: partial(bit, cycles=8, get=get_register_D, bit=6),
    0x73: partial(bit, cycles=8, get=get_register_E, bit=6),
    0x74: partial(bit, cycles=8, get=get_register_H, bit=6),
    0x75: partial(bit, cycles=8, get=get_register_L, bit=6),
    0x76: partial(bit, cycles=16, get=get_indirect_byte_HL, bit=6),
    0x77: partial(bit, cycles=8, get=get_register_A, bit=6),

    0x78: partial(bit, cycles=8, get=get_register_B, bit=7),
    0x79: partial(bit, cycles=8, get=get_register_C, bit=7),
    0x7a: partial(bit, cycles=8, get=get_register_D, bit=7),
    0x7b: partial(bit, cycles=8, get=get_register_E, bit=7),
    0x7c: partial(bit, cycles=8, get=get_register_H, bit=7),
    0x7d: partial(bit, cycles=8, get=get_register_L, bit=7),
    0x7e: partial(bit, cycles=16, get=get_indirect_byte_HL, bit=7),
    0x7f: partial(bit, cycles=8, get=get_register_A, bit=7),
}
