import argparse
import os
import re
import subprocess


CORRECT_ERRORS_PREFIXES = [
    'Control sum doesnt match',
    'No IHDR chunk',
    'Unknown filter',
    'To many palette colors',
    'There should be a palette chunk',
    'There should be only one palette chunk',
    'No IDAT chunks',
    'No IEND chunk',
    'Incorrect']


def check_pics(path, call):
    file_list = []
    for dirname, dirs, files in os.walk(path):
        file_list = [os.path.join(dirname, file)
                     for file in files if re.match(r'.+\.png', file)]

    error_count = 0
    file_count = len(file_list)

    for i, file in enumerate(file_list):
        print('{} / {}'.format(i + 1, file_count), end='\r')
        command = call + ' "' + file + '"'
        result = subprocess.run(command, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                encoding='utf-8')
        if result.returncode == 0:
            continue
        correct_error = False
        print(file, result.stderr, end='')
        for s in CORRECT_ERRORS_PREFIXES:
            if result.stderr.find(s, 0) != -1:
                correct_error = True
        if not correct_error:
            error_count += 1
            print(result.stderr, end='')
    print('error count: {} / {}'.format(error_count, file_count))


def get_parser():
    parser = argparse.ArgumentParser(
        description='Calls png reader on test pics')
    parser.add_argument('path', help='test pics directory')
    parser.add_argument('call', help='function to call without filename')
    return parser.parse_args()


def main():
    args = get_parser()
    path = args.path
    call = args.call
    check_pics(path, call)


if __name__ == '__main__':
    main()
