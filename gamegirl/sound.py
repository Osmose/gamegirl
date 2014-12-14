from memory import MappedRegister, register_attribute


class NR11(MappedRegister):
    name = 'nr11'
    reset_value = 0xbf
    read_mask = 0b11000000

    wave_duty = register_attribute(0b11000000)
    t1 = register_attribute(0b00111111)

    @property
    def sound_length(self):
        return (64 - self.t1) * (1 / 256)  # Seconds


class NR52(MappedRegister):
    name = 'nr52'
    reset_value = 0xf1
    write_mask = 0b11110000

    sound_on = register_attribute(0b10000000)
    sound_4_on = register_attribute(0b1000)
    sound_3_on = register_attribute(0b0100)
    sound_2_on = register_attribute(0b0010)
    sound_1_on = register_attribute(0b0001)


sound_ram_registers = {
    0xff11: NR11,
    0xff26: NR52,
}
