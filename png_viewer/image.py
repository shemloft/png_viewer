import struct
import math
from array import array


class Image:
    def __init__(self, reader):
        self.reader = reader
        self.header = self.reader.header
        self.bit_depth = self.header.bit_depth
        self.bit_map = []

    def get_image(self, image_rows_list):
        for row in image_rows_list:
            pixels = self._get_pixels(row)
            self.bit_map.append(pixels)

    def _get_pixels(self, pixel_line):
        bit_depth = self.header.bit_depth
        if bit_depth == 8:
            return pixel_line
        if bit_depth == 16:
            pixel_line = array.tostring(pixel_line)
            return array(
                'H',
                struct.unpack('!{}H'.format(len(pixel_line) // 2), pixel_line))

        bit_array = array('B')
        for byte in pixel_line:
            bit_str = '{:08b}'.format(byte)
            i = 0
            while i < 8:
                pix = bit_str[i:i + bit_depth]
                bit_array.append(int(pix, 2))
                i += bit_depth
        return bit_array

    def rgb_representation(self):
        color_type = self.header.color_type
        return self.RGB_FUNCTIONS[color_type](self)

    def _get_indexed_color(self):
        palette = self.reader.PLTE
        rgb_view = []
        for line in self.bit_map:
            rgb_line = [palette[i] for i in line]
            rgb_view.append(rgb_line)
        return rgb_view

    def _get_truecolor_with_alpha(self):
        rgb_view = []
        for line in self.bit_map:
            rgb_line = [line[i*4:i*4 + 4] for i in range(len(line)//4)]
            rgb_view.append(rgb_line)
        return rgb_view

    def _get_grayscale_with_alpha(self):
        rgb_view = []
        for line in self.bit_map:
            rgb_line = [(line[i*2], line[i*2], line[i*2], line[i*2+1])
                        for i in range(len(line)//2)]
            rgb_view.append(rgb_line)
        return rgb_view

    def _get_truecolor(self):
        rgb_view = []
        for line in self.bit_map:
            rgb_line = [line[i*3:i*3+3] for i in range(len(line)//3)]
            rgb_view.append(rgb_line)
        return rgb_view

    def _get_grayscale(self):
        rgb_view = []
        for line in self.bit_map:
            rgb_line = [(self._get_grayscale_rgb(i),
                         self._get_grayscale_rgb(i),
                         self._get_grayscale_rgb(i)) for i in line]
            rgb_view.append(rgb_line)
        return rgb_view

    def _get_grayscale_rgb(self, byte):
        if self.bit_depth == 8:
            return byte
        if self.bit_depth == 1:
            return bool(byte) * 255
        if self.bit_depth in (2, 4):
            color_step = 256 // (self.bit_depth ** 2 - 1)
            return (bool(byte) * 255) \
                if byte in (0, self.bit_depth ** 2 - 1) \
                else color_step * byte
        if self.bit_depth == 16:
            return byte

    RGB_FUNCTIONS = {
        0: _get_grayscale,
        2: _get_truecolor,
        3: _get_indexed_color,
        4: _get_grayscale_with_alpha,
        6: _get_truecolor_with_alpha
    }
