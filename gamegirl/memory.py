import struct


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


def register_attribute(mask):
    # Determine shift by testing bits until we find a non-zero one.
    shift = 0
    test_mask = 1
    while mask & test_mask == 0:
        shift += 1
        test_mask = test_mask << 1

    def getter(self):
        return (self.value & mask) >> shift

    def setter(self, value):
        value = value & (mask >> shift)  # Mask value to proper length.
        self.value = self.value ^ (self.value & mask)  # Clear bits.
        self.value = self.value & (value << shift)  # Write new bits.

    return property(getter, setter)


class MappedRegister(object):
    name = None
    reset_value = 0
    write_mask = 0xff
    read_mask = 0xff

    def __init__(self):
        self.value = 0

    def reset(self):
        self.value = self.reset_value

    def write(self, value):
        self.value = value & self.write_mask

    def read(self):
        return self.value & self.read_mask


class MappedRegisterMemory(object):
    def __init__(self, registers):
        self.registers = {}
        self.named_registers = {}
        for address, mapped_register in registers.items():
            register = mapped_register()
            self.registers[address] = register
            if register.name:
                self.named_registers[register.name] = register


    def read_short(self, address):
        try:
            return (self.registers[address].read() &
                    (self.registers[address + 1].read() << 8))
        except KeyError:
            raise ValueError('Missing register: ${0:02x}'.format(address))

    def read_byte(self, address):
        try:
            return self.registers[address].read()
        except KeyError:
            raise ValueError('Missing register: ${0:02x}'.format(address))

    def read_bytes(self, start_address, end_address):
        try:
            return [self.registers[address].read()
                    for address in range(start_address, end_address)]
        except KeyError:
            raise ValueError('Missing register: ${0:02x}'.format(address))

    def write_short(self, address, value):
        try:
            self.registers[address].write(value & 0xff)
            self.registers[address + 1].write((value & 0xff00) >> 8)
        except KeyError:
            raise ValueError('Missing register: ${0:02x}'.format(address))

    def write_byte(self, address, value):
        try:
            self.registers[address].write(value)
        except KeyError:
            raise ValueError('Missing register: ${0:02x}'.format(address))



class Memory(object):
    def __init__(self, rom, bios):
        from gamegirl.registers import register_map

        self.rom = rom
        self.bios = bios
        self.bios_enabled = True

        self.wram = Ram(8 * 1024)
        self.stack = Ram(127)
        self.lcd_ram = Ram(8 * 1024)
        self.wave_pattern_ram = Ram(16)

        self.io_ports = MappedRegisterMemory(register_map)

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

        # I/O Ports
        if 0xff00 <= start_address < end_address <= 0xff30:
            return self.io_ports, 0

        if 0xff30 <= start_address < end_address <= 0xff40:
            return self.wave_pattern_ram, 0xff30

        if 0xff40 <= start_address < end_address <= 0xff4c:
            return self.io_ports, 0

        # Stack RAM
        if 0xff80 <= start_address < end_address <= 0xfffe:
            return self.stack, 0xff80

        # Interrupt Enable Register
        if start_address == 0xffff:
            return self.io_ports, 0

        raise ValueError('Invalid memory range: 0x{0:04x} - 0x{1:04x}'
                         .format(start_address, end_address))
