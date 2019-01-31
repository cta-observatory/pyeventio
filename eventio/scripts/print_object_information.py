from eventio import EventIOFile
from argparse import ArgumentParser
from collections import Counter, defaultdict
import json
import warnings
from eventio.simtel import TrackingPosition, TelescopeEvent


def count_versions(f):
    c = Counter()
    try:
        for o in f:
            if isinstance(o, TrackingPosition):
                eventio_type = 2100
            elif isinstance(o, TelescopeEvent):
                eventio_type = 2200
            else:
                eventio_type = o.header.type

            c.update([(
                eventio_type,
                o.header.version,
                o.__module__ + '.' + o.__class__.__qualname__)
            ])
            if o.header.only_subobjects:
                c.update(count_versions(o))
    except EOFError:
        warnings.warn("File seems to be truncated")
    return c


def sum_up_size(f, sizes=defaultdict(int)):
    try:
        for o in f:
            if o.header.only_subobjects:
                sum_up_size(o, sizes)
            else:
                if isinstance(o, TrackingPosition):
                    eventio_type = 2100
                elif isinstance(o, TelescopeEvent):
                    eventio_type = 2200
                else:
                    eventio_type = o.header.type

                sizes[eventio_type, o.header.version] += o.header.length
    except EOFError:
        warnings.warn("File seems to be truncated")
    return sizes


parser = ArgumentParser()
parser.add_argument('inputfile')
parser.add_argument('--json', help='print json', action='store_true')


def main():
    args = parser.parse_args()

    with EventIOFile(args.inputfile) as f:
        counter = count_versions(f)
        sizes = sum_up_size(f)

    if args.json:
        object_info = [
            {'type': t, 'version': v, 'number_of_objects': c}
            for (t, v), c in sorted(list(counter.items()))
        ]
        print(json.dumps(object_info, indent=2))
    else:
        print(' Type | Version | #Objects |size in MB| eventio-class')
        print('-' * 60)
        for (t, v, q), c in sorted(list(counter.items())):
            print('{: 5d} | {: 7d} | {: 8d} | {: 8.2f} | {}'.format(
                t, v, c, sizes[t,v]/1204**2, q,
            ))
        print('-' * 60)


if __name__ == '__main__':
    main()
