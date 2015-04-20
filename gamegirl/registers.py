from memory import MappedRegister, register_attribute


class P1(MappedRegister):
    """Joypad Info"""
    name = 'p1'


class SB(MappedRegister):
    """Serial Transfer Data"""
    name = 'sb'


class SC(MappedRegister):
    """Serial I/O Control"""
    name = 'sc'


class DIV(MappedRegister):
    """Divider"""
    name = 'div'


class TIMA(MappedRegister):
    """Timer Counter"""
    name = 'tima'


class TMA(MappedRegister):
    """Timer Modulo"""
    name = 'tma'


class TAC(MappedRegister):
    """Timer Control"""
    name = 'tac'


class IF(MappedRegister):
    """Interrupt Flag"""
    name = 'if'


class NR10(MappedRegister):
    """Sound Mode 1"""
    name = 'nr10'


class NR11(MappedRegister):
    """Sound Mode 1 Length/Wave Duty"""
    name = 'nr11'
    reset_value = 0xbf
    read_mask = 0b11000000

    wave_duty = register_attribute(0b11000000)
    t1 = register_attribute(0b00111111)

    @property
    def sound_length(self):
        return (64 - self.t1) * (1 / 256)  # Seconds


class NR12(MappedRegister):
    """Sound Mode 1 Envelope"""
    name = 'nr12'


class NR13(MappedRegister):
    """Sound Mode 1 Frequency Lo"""
    name = 'nr13'


class NR14(MappedRegister):
    """Sound Mode 1 Frequency Hi"""
    name = 'nr14'


class NR21(MappedRegister):
    """Sound Mode 2 Length/Wave Duty"""
    name = 'nr21'


class NR22(MappedRegister):
    """Sound Mode 2 Envelope"""
    name = 'nr22'


class NR23(MappedRegister):
    """Sound Mode 2 Frequency Lo"""
    name = 'nr23'


class NR24(MappedRegister):
    """Sound Mode 2 Frequency Hi"""
    name = 'nr24'


class NR30(MappedRegister):
    """Sound Mode 3 On/Off"""
    name = 'nr30'


class NR31(MappedRegister):
    """Sound Mode 3 Length"""
    name = 'nr31'


class NR32(MappedRegister):
    """Sound Mode 3 Output Level"""
    name = 'nr32'


class NR33(MappedRegister):
    """Sound Mode 3 Frequency Lo"""
    name = 'nr33'


class NR34(MappedRegister):
    """Sound Mode 3 Frequency Hi"""
    name = 'nr34'


class NR41(MappedRegister):
    """Sound Mode 4 Length"""
    name = 'nr41'


class NR42(MappedRegister):
    """Sound Mode 4 Envelope"""
    name = 'nr42'


class NR43(MappedRegister):
    """Sound Mode 4 Polynomial Counter"""
    name = 'nr43'


class NR44(MappedRegister):
    """Sound Mode 4 Frequency Counter/Consecutive; Initial"""
    name = 'nr44'


class NR50(MappedRegister):
    """Channel Control / On-Off / Volume"""
    name = 'nr50'


class NR51(MappedRegister):
    """Sound Output Terminal Selection"""
    name = 'nr51'


class NR52(MappedRegister):
    """Sound On/Off"""
    name = 'nr52'
    reset_value = 0xf1
    write_mask = 0b11110000

    sound_on = register_attribute(0b10000000)
    sound_4_on = register_attribute(0b1000)
    sound_3_on = register_attribute(0b0100)
    sound_2_on = register_attribute(0b0010)
    sound_1_on = register_attribute(0b0001)


class LCDC(MappedRegister):
    """LCD Control"""
    name = 'lcdc'
    reset_value = 0x91

    bg_window_display = register_attribute(0b1)
    obj_display = register_attribute(0b10)
    obj_size = register_attribute(0b100)
    bg_tilemap_display = register_attribute(0b1000)
    bg_window_tile_data = register_attribute(0b10000)
    window_display = register_attribute(0b100000)
    window_tile_map_display = register_attribute(0b1000000)
    lcd_control = register_attribute(0b10000000)


class STAT(MappedRegister):
    """LCDC Status"""
    name = 'stat'

    mode = register_attribute(0b10)


class SCY(MappedRegister):
    """Scroll Y"""
    name = 'scy'


class SCX(MappedRegister):
    """Scroll X"""
    name = 'scx'


class LY(MappedRegister):
    """LCDC Y-Coordinate"""
    name = 'ly'


class LYC(MappedRegister):
    """LY Compare"""
    name = 'lyc'


class DMA(MappedRegister):
    """DMA Transfer and Start Address"""
    name = 'dma'


class BGP(MappedRegister):
    """BG & Window Palette Data"""
    name = 'bgp'


class OBP0(MappedRegister):
    """Object Palette 0 Data"""
    name = 'obp0'


class OBP1(MappedRegister):
    """Object Palette 1 Data"""
    name = 'obp1'


class WY(MappedRegister):
    """Window Y Position"""
    name = 'wy'


class WX(MappedRegister):
    """Window X Position"""
    name = 'wx'


class IE(MappedRegister):
    """Interrupt Enable"""
    name = 'ie'


register_map = {
    0xff00: P1,
    0xff01: SB,
    0xff02: SC,
    0xff04: DIV,
    0xff05: TIMA,
    0xff06: TMA,
    0xff07: TAC,
    0xff0f: IF,
    0xff10: NR10,
    0xff11: NR11,
    0xff12: NR12,
    0xff13: NR13,
    0xff14: NR14,
    0xff16: NR21,
    0xff17: NR22,
    0xff18: NR23,
    0xff19: NR24,
    0xff1a: NR30,
    0xff1b: NR31,
    0xff1c: NR32,
    0xff1d: NR33,
    0xff1e: NR34,
    0xff20: NR41,
    0xff21: NR42,
    0xff22: NR43,
    0xff23: NR44,
    0xff24: NR50,
    0xff25: NR51,
    0xff26: NR52,
    0xff40: LCDC,
    0xff41: STAT,
    0xff42: SCY,
    0xff43: SCX,
    0xff44: LY,
    0xff45: LYC,
    0xff46: DMA,
    0xff47: BGP,
    0xff48: OBP0,
    0xff49: OBP1,
    0xff4a: WY,
    0xff4b: WX,
    0xffff: IE,
}
