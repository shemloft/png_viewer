import struct
import os
import re
import zlib
import math
import sys
from array import array
from . import image

COLOUR_TYPES = {
    0: ('Grayscale', (1, 2, 4, 8, 16)),
    2: ('Truecolour', (8, 16)),
    3: ('Indexed-colour', (1, 2, 4, 8)),
    4: ('Grayscale with alpha', (8, 16)),
    6: ('Truecolor with alpha', (8, 16))
}

PNG_SIGNATURE = [137, 80, 78, 71, 13, 10, 26, 10]

ADAM7 = ((0, 0, 8, 8),
         (4, 0, 8, 8),
         (0, 4, 4, 8),
         (2, 0, 4, 4),
         (0, 2, 2, 4),
         (1, 0, 2, 2),
         (0, 1, 1, 2))


class Header:
    def __init__(self, width, height, bit_depth, color_type,
                 compression_method, filter_method, interlace_method):

        self.width = width
        self.height = height
        self.bit_depth = bit_depth
        self.color_type = color_type
        self.compression_method = compression_method
        self.filter_method = filter_method
        self.interlace_method = interlace_method

        self._check_info()

    def get_info(self):
        info = [('Width', self.width),
                ('Height', self.height),
                ('Bit depth', self.bit_depth),
                ('Color type', self.color_type),
                ('Compression method', self.compression_method),
                ('Filter method', self.filter_method),
                ('Interlace method', self.interlace_method)]
        return info

    def get_detailed_info(self):
        info = [('Width', self.width),
                ('Height', self.height),
                ('Bit depth', self.bit_depth),
                ('Color type', COLOUR_TYPES[self.color_type][0]),
                ('Compression method', 'deflate/inflate compression'),
                ('Filter method', 'adaptive filtering with '
                                  'five basic filter types'),
                ('Interlace method', 'no interlace'
                if not self.interlace_method else 'Adam7 interlace')]
        return info

    def _check_info(self):
        if self.width == 0 or self.height == 0:
            sys.exit('Incorrect dimensions')

        if self.color_type not in COLOUR_TYPES:
            sys.exit('Incorrect colour type: {}'.format(self.color_type))

        if self.bit_depth not in COLOUR_TYPES[self.color_type][1]:
            sys.exit('Incorrect bit depth or bit depth not matching '
                     'the color type: {}'.format(self.bit_depth))

        if self.compression_method != 0:
            sys.exit('Incorrect compression method: {}'.format(
                self.compression_method))

        if self.filter_method != 0:
            sys.exit('Incorrect filter method: {}'.format(
                self.filter_method))

        if self.interlace_method not in (0, 1):
            sys.exit('Incorrect interlace method: {}'.format(
                self.interlace_method))


def check_png_signature(signature):
    for (i, byte) in enumerate(signature):
        if byte != PNG_SIGNATURE[i]:
            sys.exit(
                'Incorrect PNG signature: {} byte should be {} '
                'but was {}'.format(i, PNG_SIGNATURE[i], byte))


class Reader:
    def __init__(self, file_name, without_decoding=False):
        self.file_name = file_name

        self.chunk_count = 0
        self.idat_count = 0
        self.chunks_list = []
        self.chunk_types = []
        self.idat_list = []
        self.PLTE = None
        self._read_file()
        self._process_chunks()
        self.image = image.Image(self)
        if not without_decoding:
            self._decode_IDAT()

    def _read_file(self):
        with open(self.file_name, 'rb') as f:
            png_signature = f.read(8)
            check_png_signature(png_signature)
            self._read_header(f)

            if self.header.interlace_method == 1:
                # TODO
                sys.exit(
                    'Sorry, this program does not work with interlaced images')

            while True:
                len_b = f.read(4)
                if len_b == '':
                    sys.exit('No IEND chunk')
                length = struct.unpack('!L', len_b)[0]
                chunk_type = f.read(4)
                data = f.read(length)
                crc = f.read(4)
                self._check_crc(chunk_type, data, crc)
                self.chunk_count += 1
                if chunk_type == b'IDAT':
                    self.idat_count += 1
                if chunk_type == b'IEND':
                    break
                else:
                    self.chunks_list.append((chunk_type, data))
                    self.chunk_types.append(chunk_type)
            self.chunks_set = set(self.chunk_types)

        if self.idat_count == 0:
            sys.exit('No IDAT chunks')

    def _process_chunks(self):
        for (chunk_type, data) in self.chunks_list:
            if chunk_type == b'PLTE':
                if self.PLTE:
                    sys.exit('There should be only one palette chunk')
                self._process_PLTE(data)
            if chunk_type == b'IDAT':
                self.idat_list.append(data)
        if self.header.color_type == 3 and not self.PLTE:
            sys.exit('There should be a palette chunk for indexed image')
        # TODO: process other chunks

    def _process_PLTE(self, data):
        if len(data) % 3 != 0:
            sys.exit('Incorrect palette chunk length')
        plte_count = len(data) // 3
        if plte_count > 2 ** self.header.bit_depth:
            sys.exit('To many palette colors: {}'.format(plte_count - 1))
        self.PLTE = {i: data[i * 3: i * 3 + 3] for i in range(plte_count)}

    def _decode_IDAT(self):
        idat_data = b''.join(self.idat_list)
        decompressed_data = zlib.decompress(idat_data)
        image_rows_list = self._undo_filter(decompressed_data)
        self.image.get_image(image_rows_list)

    def _undo_filter(self, data):
        bytes_array = array('B', data)
        image_bytes = []
        recon = None
        while len(bytes_array) >= self.row_bytes + 1:
            filter_type = bytes_array[0]
            scanline = bytes_array[1:self.row_bytes + 1]
            del bytes_array[:self.row_bytes + 1]
            recon = self._process_filter(filter_type, scanline, recon)
            image_bytes.append(recon)
        return image_bytes

    def _process_filter(self, filter_type, scanline, previous):
        if filter_type not in (0, 1, 2, 3, 4):
            sys.exit('Unknown filter: {}'.format(filter_type))

        if filter_type == 0:
            return scanline

        if not previous:
            previous = array('B', [0] * len(scanline))

        filter_unit = int(max(1, self.bytes_per_pixel))
        result_line = scanline

        def sub():
            prev_i = 0  # pixel before
            for i in range(filter_unit, len(result_line)):
                current_byte = scanline[i]
                previous_byte = result_line[prev_i]
                result_line[i] = (current_byte + previous_byte) % 256
                prev_i += 1

        def up():
            for i in range(len(result_line)):
                current_byte = scanline[i]
                above_byte = previous[i]
                result_line[i] = (current_byte + above_byte) % 256

        def average():
            prev_i = -filter_unit
            for i in range(len(result_line)):
                current_byte = scanline[i]
                if prev_i < 0:
                    previous_byte = 0
                else:
                    previous_byte = result_line[prev_i]
                above_byte = previous[i]
                result_line[i] = (current_byte +
                                  ((previous_byte + above_byte) >> 1)) % 256
                prev_i += 1

        def paeth():
            prev_i = -filter_unit
            for i in range(len(result_line)):
                current_byte = scanline[i]
                if prev_i < 0:
                    previous_byte = previous_above_byte = 0
                else:
                    previous_byte = result_line[prev_i]
                    previous_above_byte = previous[prev_i]
                above_byte = previous[i]
                p = previous_byte + above_byte - previous_above_byte
                pa = abs(p - previous_byte)
                pb = abs(p - above_byte)
                pc = abs(p - previous_above_byte)
                if pa <= pb and pa <= pc:
                    pr = previous_byte
                elif pb <= pc:
                    pr = above_byte
                else:
                    pr = previous_above_byte
                result_line[i] = (current_byte + pr) % 256
                prev_i += 1

        if filter_type == 1:
            sub()
        if filter_type == 2:
            up()
        if filter_type == 3:
            average()
        if filter_type == 4:
            paeth()

        return result_line

    def _read_header(self, f):
        header_len_b = f.read(4)
        if header_len_b == '':
            sys.exit('No IHDR chunk')
        header_len = struct.unpack('!L', header_len_b)[0]
        chunk_type = f.read(4)
        if chunk_type != b'IHDR':
            sys.exit('No IHDR chunk')
        if header_len != 13:
            sys.exit('Incorrect IHDR chunk length')

        self.chunk_count += 1
        data = f.read(13)

        self.header = Header(
            struct.unpack('!L', data[0:4])[0],
            struct.unpack('!L', data[4:8])[0],
            struct.unpack('B', data[8:9])[0],
            struct.unpack('B', data[9:10])[0],
            struct.unpack('B', data[10:11])[0],
            struct.unpack('B', data[11:12])[0],
            struct.unpack('B', data[12:])[0]
        )

        header_crc = f.read(4)
        self._check_crc(chunk_type, data, header_crc)

        color_channels = (3 if self.header.color_type in (2, 6) else 1)
        alpha = (1 if self.header.color_type in (4, 6) else 0)
        self.total_samples_count = color_channels + alpha
        self.bytes_per_pixel = (self.header.bit_depth / float(8)) * \
                               (self.total_samples_count)
        self.row_bytes = int(
            math.ceil(self.header.width * self.bytes_per_pixel))

    def _check_crc(self, chunk_type, data, crc):
        counted_crc = zlib.crc32(chunk_type + data)
        actual_crc = struct.unpack('!L', crc)[0]
        if counted_crc != actual_crc:
            sys.exit(
                'Control sum doesnt match at {} chunk, '
                'chunk type: {}'.format(self.chunk_count, chunk_type))
