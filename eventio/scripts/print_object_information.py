from eventio import EventIOFile
from argparse import ArgumentParser
from collections import Counter, namedtuple
import json
import warnings
from eventio.simtel import TrackingPosition, TelescopeEvent


ObjectInfo = namedtuple('ObjectInfo', ['type', 'version', 'level', 'name'])



def count_versions(f, level=0):
    c = Counter()
    try:
        for o in f:
            if isinstance(o, TrackingPosition):
                eventio_type = 2100
            elif isinstance(o, TelescopeEvent):
                eventio_type = 2200
            else:
                eventio_type = o.header.type

            c.update([ObjectInfo(
                type=eventio_type,
                level=level,
                version=o.header.version,
                name=(o.__module__ + '.' + o.__class__.__qualname__)[8:],
            )])
            if o.header.only_subobjects:
                c.update(count_versions(o, level=level + 1))
    except EOFError:
        warnings.warn("File seems to be truncated")
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
            {**info._asdict(), 'number_of_objects': c}
            for info, c in sorted(list(counter.items()))
        ]
        print(json.dumps(object_info, indent=2))
    else:
        print(' Type | Version | Level | #Objects | eventio-class')
        print('-' * 60)
        for info, count in sorted(list(counter.items())):
            print('{type: 5d} | {version: 7d} | {level: 5d} | {count: 8d} | {name}'.format(
                **info._asdict(), count=count,
            ))
        print('-' * 60)


if __name__ == '__main__':
    main()
