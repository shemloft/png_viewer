import urllib.request
import zipfile
import argparse


def extract_pictures(archive, path):
    z = zipfile.ZipFile(archive, 'r')
    z.extractall(path)


def get_archive(url, filename):
    with urllib.request.urlopen(url) as u:
        with open(filename, 'wb') as f:
            f.write(u.read())


def get_parser():
    parser = argparse.ArgumentParser(
        description='Pictures downloader and unpacker')
    parser.add_argument('link', help='file archive link')
    return parser.parse_args()


def main():
    filename = 'png_test_pics.zip'
    path = 'png_test_pics'
    args = get_parser()
    url = args.link
    get_archive(url, filename)
    extract_pictures(filename, path)


if __name__ == '__main__':
    main()
