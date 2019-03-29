from ..base import EventIOFile, EventIOObject
from ..search_utils import yield_all_objects_depth_first
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument('inputfile')
parser.add_argument(
    '-m', '--max-repeats',
    default=5,
    type=int,
    help='If many of the same objects follow each other, only print the first `max-repeats` objects'
)
parser.add_argument(
    '-r', '--repr',
    action='store_true',
    help='Print low-level object information'
)


def main():
    args = parser.parse_args()

    conv = str if not args.repr else repr

    with EventIOFile(args.inputfile) as f:
        last = None
        last_level = 0
        n_same = 0

        try:
            for o, level in yield_all_objects_depth_first(f):
                if last and last != EventIOObject and isinstance(o, last):
                    n_same += 1
                    last_level = level
                else:
                    last = o.__class__
                    if n_same > args.max_repeats:
                        print(
                            '    ' * last_level,
                            'And {} objects more of the same type'.format(
                                n_same - args.max_repeats
                            )
                        )
                    n_same = 0
                    last_level = level

                if n_same < args.max_repeats:
                    print('    ' * level, conv(o))
        except EOFError as e:
            print(e)


if __name__ == '__main__':
    main()
