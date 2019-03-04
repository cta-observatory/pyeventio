'''
Cleanly cut an eventio file, so that the
uncompressed size is at most `max_size`
'''
from argparse import ArgumentParser
import re
import gzip
from ..base import EventIOFile


parser = ArgumentParser(description=__doc__)
parser.add_argument('inputfile', help='Input eventio file')
parser.add_argument(
    'outputfile',
    help='Output file, if ending with .gz, it is written gzip compressed'
)
parser.add_argument(
    'max_size',
    help=(
        'Maximimum, uncompressed output file size.'
        ' You can use k, M, G suffixes.'
        ' As many complete top-level objects are written, so that max_size is'
        ' not exceeded'
    )
)


def parse_size(size):
    m = re.match(r'(\d+)([kMG])?', size)
    if not m:
        raise ValueError('Format not recognized, valid are #, #k, #M or #G')

    size, unit = m.groups()
    size = float(size)

    if unit is None:
        return int(size)

    if unit == 'k':
        return int(size * 1024)

    if unit == 'M':
        return int(size * 1024**2)

    if unit == 'G':
        return int(size * 1024**3)


def main():
    args = parser.parse_args()

    max_size = parse_size(args.max_size)
    bytes_to_read = 0
    with EventIOFile(args.inputfile) as f:
        last_o = None
        for o in f:
            last_byte = o.header.content_address + o.header.content_size
            if last_byte < max_size:
                bytes_to_read = last_byte
                last_o = o
            else:
                break

    print('Writing {:.2f}MB (uncompressed)'.format(bytes_to_read / 1024**2))
    print('Last object is of type {}'.format(last_o.header.type))

    if args.outputfile.endswith('.gz'):
        open_file = gzip.open
    else:
        open_file = open

    with open_file(args.outputfile, 'wb') as of:

        with EventIOFile(args.inputfile) as f:
            of.write(f.read(bytes_to_read))


if __name__ == '__main__':
    main()
