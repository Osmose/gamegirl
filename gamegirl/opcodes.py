from functools import partial, wraps


## Reading Values ######################################################

def get_immediate_byte(cpu):
    value = cpu.read_next_byte()
    if cpu.debug:
        cpu.debug_kwargs['source'] = '${0:02x}'.format(value)

    return value


def get_immediate_short(cpu):
    value = cpu.read_next_short()
    if cpu.debug:
        cpu.debug_kwargs['source'] = '${0:04x}'.format(value)

    return value


def get_register(cpu, register):
    if cpu.debug:
        cpu.debug_kwargs['source'] = register

    return getattr(cpu, register)


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
get_register_PC = partial(get_register, register='PC')


def get_indirect_byte(cpu, register):
    if cpu.debug:
        cpu.debug_kwargs['source'] = '({0})'.format(register)

    address = getattr(cpu, register)
    return cpu.memory.read_byte(address)


get_indirect_byte_HL = partial(get_indirect_byte, register='HL')
get_indirect_byte_BC = partial(get_indirect_byte, register='BC')
get_indirect_byte_DE = partial(get_indirect_byte, register='DE')


def get_indirect_byte_immediate(cpu):
    address = cpu.read_next_short()
    if cpu.debug:
        cpu.debug_kwargs['source'] = '(${0:04x})'.format(address)

    return cpu.memory.read_byte(address)


def get_indirect_offset_byte_immediate(cpu):
    offset = cpu.read_next_byte()
    if cpu.debug:
        cpu.debug_kwargs['source'] = '($ff00+${0:02x})'.format(offset)

    return cpu.memory.read_byte(0xff00 + offset)


## Writing Values ######################################################

def write_register(cpu, register, value):
    setattr(cpu, register, value)

    if cpu.debug:
        cpu.debug_kwargs['destination'] = register


write_register_A = partial(write_register, register='A')
write_register_B = partial(write_register, register='B')
write_register_C = partial(write_register, register='C')
write_register_D = partial(write_register, register='D')
write_register_E = partial(write_register, register='E')
write_register_H = partial(write_register, register='H')
write_register_L = partial(write_register, register='L')
write_register_AF = partial(write_register, register='AF')
write_register_BC = partial(write_register, register='BC')
write_register_DE = partial(write_register, register='DE')
write_register_HL = partial(write_register, register='HL')
write_register_SP = partial(write_register, register='SP')


def write_indirect_byte(cpu, register, value):
    address = getattr(cpu, register)
    cpu.memory.write_byte(address, value)

    if cpu.debug:
        cpu.debug_kwargs['destination'] = '({0})'.format(register)


write_indirect_byte_BC = partial(write_indirect_byte, register='BC')
write_indirect_byte_DE = partial(write_indirect_byte, register='DE')
write_indirect_byte_HL = partial(write_indirect_byte, register='HL')


def write_indirect_byte_immediate(cpu, value):
    address = cpu.read_next_short()
    cpu.memory.write_byte(address, value)

    if cpu.debug:
        cpu.debug_kwargs['destination'] = '(${0:04x})'.format(address)


def write_indirect_offset_byte(cpu, register, value):
    address = 0xff00 + getattr(cpu, register)
    cpu.memory.write_byte(address, value)

    if cpu.debug:
        cpu.debug_kwargs['destination'] = '($ff00+{0})'.format(register)


write_indirect_offset_byte_C = partial(write_indirect_offset_byte, register='C')


def write_indirect_offset_byte_immediate(cpu, value):
    offset = cpu.read_next_byte()
    cpu.memory.write_byte(0xff00 + offset, value)

    if cpu.debug:
        cpu.debug_kwargs['destination'] = '($ff00+${0:02x})'.format(offset)


def write_indirect_decrement(cpu, register, value):
    address = getattr(cpu, register)
    cpu.memory.write_byte(address, value)
    setattr(cpu, register, address - 1)

    if cpu.debug:
        cpu.debug_kwargs['destination'] = '({0}-)'.format(register)


write_indirect_decrement_HL = partial(write_indirect_decrement, register='HL')


def write_indirect_increment(cpu, register, value):
    address = getattr(cpu, register)
    cpu.memory.write_byte(address, value)
    setattr(cpu, register, address + 1)

    if cpu.debug:
        cpu.debug_kwargs['destination'] = '({0}+)'.format(register)


write_indirect_increment_HL = partial(write_indirect_increment, register='HL')


## Checking Flags ######################################################

def is_flag_set(flag, cpu):
    if cpu.debug:
        cpu.debug_kwargs['condition'] = flag
    return bool(getattr(cpu, 'flag_' + flag))


is_flag_Z_set = partial(is_flag_set, 'Z')
is_flag_N_set = partial(is_flag_set, 'N')
is_flag_H_set = partial(is_flag_set, 'H')
is_flag_C_set = partial(is_flag_set, 'C')


def is_flag_reset(flag, cpu):
    if cpu.debug:
        cpu.debug_kwargs['condition'] = 'N' + flag
    return not bool(getattr(cpu, 'flag_' + flag))


is_flag_Z_reset = partial(is_flag_reset, 'Z')
is_flag_N_reset = partial(is_flag_reset, 'N')
is_flag_H_reset = partial(is_flag_reset, 'H')
is_flag_C_reset = partial(is_flag_reset, 'C')


## Instructions ########################################################

def instruction(debug_string):
    """
    Decorator for instructions that handles running CPU cycles and
    setting up debug logging if necessary.
    """
    def decorator(func):
        @wraps(func)
        def wrapped(**kwargs):
            cycles = kwargs.pop('cycles', None)
            cpu = kwargs.get('cpu')

            # Set up debug logging first, in case the operation wants
            # to override anything (ex: RLA overriding debug string).
            if cpu and cpu.debug:
                cpu.debug_string = debug_string
                cpu.debug_kwargs.update(kwargs)

            # Execute instruction.
            func(**kwargs)

            # Run cycles if specified.
            if cpu and cycles:
                cpu.cycle(cycles)

        return wrapped
    return decorator


@instruction('LD {destination},{source}')
def load(cpu, get, write):
    value = get(cpu=cpu)
    write(cpu=cpu, value=value)


@instruction('PUSH {source}')
def push_short(cpu, get):
    value = get(cpu=cpu)
    cpu.stack.push_short(value)


@instruction('POP {destination}')
def pop_short(cpu, write):
    value = cpu.stack.pop_short()
    write(cpu=cpu, value=value)


@instruction('XOR {source}')
def xor(cpu, get):
    value = get(cpu=cpu)
    cpu.A = cpu.A ^ value

    cpu.flag_Z = cpu.A == 0
    cpu.flag_N = 0
    cpu.flag_H = 0
    cpu.flag_C = 0


@instruction('SWAP {source}')
def swap(cpu, get, write):
    value = get(cpu=cpu)
    result = (value >> 4) & (value << 4)
    write(cpu=cpu, value=result)

    cpu.flag_Z = result == 0
    cpu.flag_N = 0
    cpu.flag_H = 0
    cpu.flag_C = 0


@instruction('JR {condition},{source}')
def jump_condition(cpu, get, condition):
    value = get(cpu=cpu)
    if condition(cpu=cpu):
        cpu.PC += value


def cb_dispatch(cpu):
    """Dispatch to special CB prefix table of opcodes."""
    opcode = cpu.read_next_byte()
    try:
        return CB_OPCODES[opcode](cpu=cpu)
    except KeyError:
        raise ValueError('Invalid CB opcode: ${0:02x}'.format(opcode))


@instruction('BIT {bit},{source}')
def bit(cpu, get, bit):
    value = get(cpu=cpu)
    result = (value >> bit) & 0x1
    cpu.flag_Z = result == 0
    cpu.flag_N = 0
    cpu.flag_H = 1


@instruction('INC {source}')
def increment(cpu, get, write):
    value = get(cpu=cpu)
    write(cpu=cpu, value=value + 1)


@instruction('DEC {source}')
def decrement(cpu, get, write):
    value = get(cpu=cpu)
    write(cpu=cpu, value=value - 1)


@instruction('CALL {source}')
def call(cpu, get):
    address = get(cpu=cpu)
    cpu.stack.push_short(cpu.PC)
    cpu.PC = address


@instruction('RET')
def op_return(cpu):
    address = cpu.stack.pop_short()
    cpu.PC = address


@instruction('RET {condition}')
def op_return_condition(cpu, condition):
    result = condition(cpu=cpu)
    if result:
        op_return(cpu=cpu)


@instruction('RL {source}')
def rotate_left(cpu, get, write, rla=False):
    value = get(cpu=cpu)
    result = value << 1
    write(cpu=cpu, value=result)
    cpu.flag_Z = result == 0
    cpu.flag_N = 0
    cpu.flag_H = 0
    cpu.flag_C = value & 0b10000000

    # RLA special case for logging.
    if cpu.debug and rla:
        cpu.debug_string = 'RLA'


@instruction('CP {source}')
def compare(cpu, get):
    value = get(cpu=cpu)
    result = cpu.A - value
    cpu.flag_Z = result == 0
    cpu.flag_N = 1
    cpu.flag_H = (((value & 0xf) + (cpu.A & 0xf)) & 0x10) >> 1
    cpu.flag_C = result > 0


@instruction('AND {source}')
def op_and(cpu, get):
    value = get(cpu=cpu)
    cpu.A = value & cpu.A
    cpu.flag_Z = cpu.A == 0
    cpu.flag_N = 0
    cpu.flag_H = 1
    cpu.flag_C = 0


@instruction('SLA {source}')
def shift_left_reset_lsb(cpu, get, write):
    value = get(cpu=cpu)
    cpu.flag_C = (0b10000000 & value) >> 7
    write(cpu=cpu, value=value << 1)


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

    0xf1: partial(pop_short, cycles=12, write=write_register_AF),
    0xc1: partial(pop_short, cycles=12, write=write_register_BC),
    0xd1: partial(pop_short, cycles=12, write=write_register_DE),
    0xe1: partial(pop_short, cycles=12, write=write_register_HL),

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

    0x47: partial(load, cycles=4, get=get_register_A, write=write_register_B),
    0x4f: partial(load, cycles=4, get=get_register_A, write=write_register_C),
    0x57: partial(load, cycles=4, get=get_register_A, write=write_register_D),
    0x5f: partial(load, cycles=4, get=get_register_A, write=write_register_E),
    0x67: partial(load, cycles=4, get=get_register_A, write=write_register_H),
    0x6f: partial(load, cycles=4, get=get_register_A, write=write_register_L),
    0x02: partial(load, cycles=8, get=get_register_A, write=write_indirect_byte_BC),
    0x12: partial(load, cycles=8, get=get_register_A, write=write_indirect_byte_DE),
    0x77: partial(load, cycles=8, get=get_register_A, write=write_indirect_byte_HL),
    0xea: partial(load, cycles=16, get=get_register_A, write=write_indirect_byte_immediate),

    0x32: partial(load, cycles=8, get=get_register_A, write=write_indirect_decrement_HL),
    0xe2: partial(load, cycles=8, get=get_register_A, write=write_indirect_offset_byte_C),
    0xe0: partial(load, cycles=12, get=get_register_A, write=write_indirect_offset_byte_immediate),
    0xf0: partial(load, cycles=12, get=get_indirect_offset_byte_immediate, write=write_register_A),

    0x22: partial(load, cycles=8, get=get_register_A, write=write_indirect_increment_HL),

    0xcb: cb_dispatch,
    0xcd: partial(call, cycles=12, get=get_immediate_short),
    0xc9: partial(op_return, cycles=8),

    0xc0: partial(op_return_condition, cycles=8, condition=is_flag_Z_reset),
    0xc8: partial(op_return_condition, cycles=8, condition=is_flag_Z_set),
    0xd0: partial(op_return_condition, cycles=8, condition=is_flag_C_reset),
    0xd8: partial(op_return_condition, cycles=8, condition=is_flag_C_set),

    0x20: partial(jump_condition, cycles=8, get=get_immediate_byte, condition=is_flag_Z_reset),
    0x28: partial(jump_condition, cycles=8, get=get_immediate_byte, condition=is_flag_Z_set),
    0x30: partial(jump_condition, cycles=8, get=get_immediate_byte, condition=is_flag_C_reset),
    0x38: partial(jump_condition, cycles=8, get=get_immediate_byte, condition=is_flag_C_set),

    0x3c: partial(increment, cycles=4, get=get_register_A, write=write_register_A),
    0x04: partial(increment, cycles=4, get=get_register_B, write=write_register_B),
    0x0c: partial(increment, cycles=4, get=get_register_C, write=write_register_C),
    0x14: partial(increment, cycles=4, get=get_register_D, write=write_register_D),
    0x1c: partial(increment, cycles=4, get=get_register_E, write=write_register_E),
    0x24: partial(increment, cycles=4, get=get_register_H, write=write_register_H),
    0x2c: partial(increment, cycles=4, get=get_register_L, write=write_register_L),
    0x34: partial(increment, cycles=12, get=get_indirect_byte_HL, write=write_indirect_byte_HL),
    0x03: partial(increment, cycles=8, get=get_register_BC, write=write_register_BC),
    0x13: partial(increment, cycles=8, get=get_register_DE, write=write_register_DE),
    0x23: partial(increment, cycles=8, get=get_register_HL, write=write_register_HL),
    0x33: partial(increment, cycles=8, get=get_register_SP, write=write_register_SP),

    0x3d: partial(decrement, cycles=4, get=get_register_A, write=write_register_A),
    0x05: partial(decrement, cycles=4, get=get_register_B, write=write_register_B),
    0x0d: partial(decrement, cycles=4, get=get_register_C, write=write_register_C),
    0x15: partial(decrement, cycles=4, get=get_register_D, write=write_register_D),
    0x1d: partial(decrement, cycles=4, get=get_register_E, write=write_register_E),
    0x25: partial(decrement, cycles=4, get=get_register_H, write=write_register_H),
    0x2d: partial(decrement, cycles=4, get=get_register_L, write=write_register_L),
    0x35: partial(decrement, cycles=12, get=get_indirect_byte_HL, write=write_indirect_byte_HL),

    0x17: partial(rotate_left, cycles=4, get=get_register_A, write=write_register_A, rla=True),

    0xbf: partial(compare, cycles=4, get=get_register_A),
    0xb8: partial(compare, cycles=4, get=get_register_B),
    0xb9: partial(compare, cycles=4, get=get_register_C),
    0xba: partial(compare, cycles=4, get=get_register_D),
    0xbb: partial(compare, cycles=4, get=get_register_E),
    0xbc: partial(compare, cycles=4, get=get_register_H),
    0xbd: partial(compare, cycles=4, get=get_register_L),
    0xbe: partial(compare, cycles=8, get=get_indirect_byte_HL),
    0xfe: partial(compare, cycles=8, get=get_immediate_byte),

    0xa7: partial(op_and, cycles=4, get=get_register_A),
    0xa0: partial(op_and, cycles=4, get=get_register_B),
    0xa1: partial(op_and, cycles=4, get=get_register_C),
    0xa2: partial(op_and, cycles=4, get=get_register_D),
    0xa3: partial(op_and, cycles=4, get=get_register_E),
    0xa4: partial(op_and, cycles=4, get=get_register_H),
    0xa5: partial(op_and, cycles=4, get=get_register_L),
    0xa6: partial(op_and, cycles=8, get=get_indirect_byte_HL),
    0xe6: partial(op_and, cycles=8, get=get_immediate_byte),
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

    0x17: partial(rotate_left, cycles=8, get=get_register_A, write=write_register_A),
    0x10: partial(rotate_left, cycles=8, get=get_register_B, write=write_register_B),
    0x11: partial(rotate_left, cycles=8, get=get_register_C, write=write_register_C),
    0x12: partial(rotate_left, cycles=8, get=get_register_D, write=write_register_D),
    0x13: partial(rotate_left, cycles=8, get=get_register_E, write=write_register_E),
    0x14: partial(rotate_left, cycles=8, get=get_register_H, write=write_register_H),
    0x15: partial(rotate_left, cycles=8, get=get_register_L, write=write_register_L),
    0x16: partial(rotate_left, cycles=16, get=get_indirect_byte_HL, write=write_indirect_byte_HL),

    0x27: partial(shift_left_reset_lsb, cycles=8, get=get_register_A, write=write_register_A),
    0x20: partial(shift_left_reset_lsb, cycles=8, get=get_register_B, write=write_register_B),
    0x21: partial(shift_left_reset_lsb, cycles=8, get=get_register_C, write=write_register_C),
    0x22: partial(shift_left_reset_lsb, cycles=8, get=get_register_D, write=write_register_D),
    0x23: partial(shift_left_reset_lsb, cycles=8, get=get_register_E, write=write_register_E),
    0x24: partial(shift_left_reset_lsb, cycles=8, get=get_register_H, write=write_register_H),
    0x25: partial(shift_left_reset_lsb, cycles=8, get=get_register_L, write=write_register_L),
    0x26: partial(shift_left_reset_lsb, cycles=16, get=get_indirect_byte_HL, write=write_indirect_byte_HL),
}
