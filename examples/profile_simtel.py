import cProfile
import pstats
from io import StringIO
from eventio import SimTelFile
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('inputfile')
parser.add_argument('-s', '--sort', default='cumtime')
parser.add_argument('-l', '--limit', default=50, type=int)
parser.add_argument('-t', '--telescopes')
args = parser.parse_args()


if args.telescopes:
    allowed_telescopes = set(map(int, args.telescopes.split(',')))
    print(allowed_telescopes)
else:
    allowed_telescopes = None

pr = cProfile.Profile()
pr.enable()

with SimTelFile(args.inputfile, allowed_telescopes=allowed_telescopes) as f:
    for e in f:
        # print(e['telescope_events'].keys())
        pass

pr.disable()
s = StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats(args.sort)

ps.print_stats(args.limit)
print(s.getvalue())
