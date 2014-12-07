from memory import MappedRegister, register_attribute


class NR52(MappedRegister):
    name = 'nr52'
    reset_value = 0xf1
    mask = 0xf0

    sound_on = register_attribute(0x80, 7)
    sound_4_on = register_attribute(0x08, 3)
    sound_3_on = register_attribute(0x04, 2)
    sound_2_on = register_attribute(0x02, 1)
    sound_1_on = register_attribute(0x01, 0)


sound_ram_registers = {
    0xff26: NR52,
}
