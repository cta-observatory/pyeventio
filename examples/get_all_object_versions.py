from eventio import EventIOFile
from argparse import ArgumentParser
from collections import Counter


def count_versions(f):
    c = Counter()
    for o in f:
        c.update([(o.header.type, o.header.version)])
        if o.header.only_subobjects:
            c.update(count_versions(o))
    return c


parser = ArgumentParser()
parser.add_argument('inputfile')
args = parser.parse_args()

with EventIOFile(args.inputfile) as f:
    counter = count_versions(f)
    for (t, v), c in sorted(list(counter.items())):
        print(f'Type = {t}, Version = {v}, #={c}')
