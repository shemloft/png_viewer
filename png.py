import argparse
from png_viewer import png_reader, png_window


def get_parser():
    parser = argparse.ArgumentParser(description='PNG decoder and viewer')
    parser.add_argument(
        '-c', '--console', choices=[0, 1, 2], type=int, dest='console_mode',
        help='show file info in console (at least one mode should be chosen)\n'
             '0: only header info without description\n'
             '1: only header info with description\n'
             '2: header info with description and pixels colors')
    parser.add_argument(
        '-v', '--visual', action='store_true', dest='visual_mode',
        help='show file visualisation (at least one mode should be chosen)')
    parser.add_argument('file_name', help='png file name')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    file_name = args.file_name
    console_mode = args.console_mode
    visual_mode = args.visual_mode

    if console_mode is None and not visual_mode:
        parser.error('At least one mode should be chosen')

    png = png_reader.Reader(
        file_name, console_mode in (0, 1) and not visual_mode)

    if console_mode is not None:
        info = png.header.get_info() if not console_mode \
            else png.header.get_detailed_info()
        for i in info:
            print('{}: {}'.format(*i))
        if console_mode == 2:
            print(png.image.rgb_representation())
            print([tuple(pixel.tolist())
                   for line in png.image.rgb_representation()
                   for pixel in line])

    if visual_mode:
        png_window.show_window(
            png.image.rgb_representation(), png.image.header)


if __name__ == '__main__':
    main()
