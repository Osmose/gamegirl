def get_bit(byte, bit):
    return (byte & (2 ** bit)) >> bit
