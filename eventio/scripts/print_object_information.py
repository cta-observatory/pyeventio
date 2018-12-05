from eventio import EventIOFile
from argparse import ArgumentParser
from collections import Counter
import json


def count_versions(f):
    c = Counter()
    for o in f:
        c.update([(o.header.type, o.header.version)])
        if o.header.only_subobjects:
            c.update(count_versions(o))
    return c


parser = ArgumentParser()
parser.add_argument('inputfile')
parser.add_argument('--json', help='print json', action='store_true')


def main():
    args = parser.parse_args()

    with EventIOFile(args.inputfile) as f:
        counter = count_versions(f)

    if args.json:
        object_info = [
            {'type': t, 'version': v, 'number_of_objects': c}
            for (t, v), c in sorted(list(counter.items()))
        ]
        print(json.dumps(object_info, indent=2))
    else:
        print(' Type | Version | #Objects')
        print('--------------------------')
        for (t, v), c in sorted(list(counter.items())):
            print('{: 5d} | {: 7d} | {: 8d}'.format(
                t, v, c
            ))
        print('--------------------------')


if __name__ == '__main__':
    main()
