from gamegirl.utils import get_bit


class TilePatternTable(object):
    """Table of bitmap data for BG tiles."""
    def __init__(self, data, signed):
        self.data = data
        self.signed = signed

        self.tiles = []
        for index in range(256):
            start = index * 16
            self.tiles.append(Tile(data[start:start+16]))

    def get_tile(self, index):
        if self.signed:
            index += 127
        return self.tiles[index]


class Tile(object):
    """Bitmap data for a BG tile."""
    def __init__(self, data):
        self.data = data

    def get_pixel(self, x, y):
        start = y * 2
        bytes = self.data[start:start+1]
        return get_bit(bytes[0], x) & (get_bit(bytes[1], x) << 1)


class Background(object):
    def __init__(self, cpu):
        self.cpu = cpu
        self.unsigned_tiles = TilePatternTable(cpu.memory.get_view(0x8000, 0x9000))
        self.signed_tiles = TilePatternTable(cpu.memory.get_view(0x8800, 0x9800))
        self.bg_tilemap_1 = cpu.memory.get_view(0x9800, 0x9c00)
        self.bg_tilemap_2 = cpu.memory.get_view(0x9c00, 0xa000)

    @property
    def tiles(self):
        if self.cpu.memory.lcdc.bg_window_tile_data:
            return self.unsigned_tiles
        else:
            return self.signed_tiles

    @property
    def tilemap(self):
        if self.cpu.memory.lcdc.bg_tilemap_display:
            return self.bg_tilemap_2
        else:
            return self.bg_tilemap_1

    def get_pixel(self, x, y):
        x = (x + self.cpu.memory.scx) % 256
        y = (y + self.cpu.memory.scy) % 256
        tile_x, pixel_x_offset = divmod(x, 8)
        tile_y, pixel_y_offset = divmod(y, 8)

        # TODO: Ensure that tile_x and tile_y are signed when
        # bg_window_tile_data is false.
        tile_index = self.tilemap[tile_x + (tile_y * 32)]
        tile = self.tiles[tile_index]
        return tile.get_pixel(pixel_x_offset, pixel_y_offset)


class Graphics(object):
    def __init__(self, cpu):
        self.cpu = cpu
        self.background = Background(cpu)
