from eventio import EventIOFile
from eventio.search_utils import yield_all_objects_depth_first
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument('inputfile')
parser.add_argument(
    '-m', '--max-repeats',
    default=5,
    type=int,
    help='If many of the same objects follow each other, only print the first `max-repeats` objects'
)


def main():
    args = parser.parse_args()

    with EventIOFile(args.inputfile) as f:
        last = None
        last_level = 0
        n_same = 0
        for o, level in yield_all_objects_depth_first(f):

            if last and isinstance(o, last):
                n_same += 1
                last_level = level
            else:
                last = o.__class__
                if n_same > args.max_repeats:
                    print('    ' * last_level, 'And {} objects more of the same type'.format(
                        n_same - args.max_repeats
                    ))
                n_same = 0
                last_level = level

            if n_same < args.max_repeats:
                print('    ' * level, o)


if __name__ == '__main__':
    main()
