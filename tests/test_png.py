import unittest
import sys
import os
import random
import struct
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir, 'png_viewer'))
from png_viewer import png_reader, image


class PNGReaderTests(unittest.TestCase):
    def _get_header_info(self, info_tuple):
        return {
            'width': info_tuple[0],
            'height': info_tuple[1],
            'bit_depth': info_tuple[2],
            'color_type': info_tuple[3],
            'compression_method': info_tuple[4],
            'filter_method': info_tuple[5],
            'interlace_method': info_tuple[6]
        }

    def test_correct_signature(self):
        correct_signature = struct.pack(
            "8B", 137, 80, 78, 71, 13, 10, 26, 10)
        png_reader.check_png_signature(correct_signature)
        self.assertTrue(True)

    def test_incorrect_signature(self):
        incorrect_signature = struct.pack(
            "8B", 137, 80, 74, 71, 13, 10, 26, 10)
        self.assertRaises(
            ValueError,
            png_reader.check_png_signature,
            incorrect_signature)

    def test_zero_width(self):
        self.assertRaises(
            ValueError,
            png_reader.check_header_info,
            self._get_header_info((0, 32, 8, 0, 0, 0, 0)))

    def test_zero_height(self):
        self.assertRaises(
            ValueError,
            png_reader.check_header_info,
            self._get_header_info((32, 0, 8, 0, 0, 0, 0)))

    def test_unknown_color_type(self):
        self.assertRaises(
            ValueError,
            png_reader.check_header_info,
            self._get_header_info((32, 32, 8, 10, 0, 0, 0)))

    def test_incorrect_bit_depth(self):
        self.assertRaises(
            ValueError,
            png_reader.check_header_info,
            self._get_header_info((32, 32, 3, 0, 0, 0, 0)))

    def test_unmatching_color_type_and_bit_depth(self):
        self.assertRaises(
            ValueError,
            png_reader.check_header_info,
            self._get_header_info((32, 32, 4, 2, 0, 0, 0)))

    def test_incorrect_compression_method(self):
        self.assertRaises(
            ValueError,
            png_reader.check_header_info,
            self._get_header_info((32, 32, 8, 0, 5, 0, 0)))

    def test_incorrect_filter_method(self):
        self.assertRaises(
            ValueError,
            png_reader.check_header_info,
            self._get_header_info((32, 32, 8, 0, 0, 6, 0)))

    def test_incorrect_interlace_method(self):
        self.assertRaises(
            ValueError,
            png_reader.check_header_info,
            self._get_header_info((32, 32, 8, 0, 0, 0, 7)))

    def test_correct_header(self):
        png_reader.check_header_info(
            self._get_header_info((32, 32, 8, 0, 0, 0, 1)))
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
